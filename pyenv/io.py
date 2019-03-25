import io
import socket
import queue
import selectors
import logging
import threading
from pyenv.protocol import JsonProtocol, Message

class SocketSplitter:

  def __init__(self, protocol : JsonProtocol,
               sock : socket.socket,
               command_handlers : dict = None,
               sock_write_source : queue.Queue = None,
               sock_stdin_dest : queue.Queue = None,
               sock_stdout_dest : queue.Queue = None,
               sock_stderr_dest : queue.Queue = None):
    self.protocol = protocol
    self.sock = sock
    self.command_handlers = command_handlers
    self.sock_write_source = sock_write_source
    self.sock_stdin_dest = sock_stdin_dest
    self.sock_stdout_dest = sock_stdout_dest
    self.sock_stderr_dest = sock_stderr_dest

  def sock_reader(self):
    buffer = bytearray()
    while True:
      new_data = yield
      new_data : bytes
      for b in new_data:
        buffer.append(b)
        if b == self.protocol.sep:
          self.read_handler(buffer)
          buffer = bytearray()

  def sock_writer(self):
    while True:
      try:
        head = self.sock_write_source.get_nowait()
        encoded = self.protocol.encode(head)
        while len(encoded) > 0:
          sent = self.sock.send(encoded)
          yield
          encoded = encoded[sent:]
      except queue.Empty:
        yield

  # TODO: read_handler should be client/host specific
  def read_handler(self, buffer : bytearray):
    try:
      decoded = self.protocol.decode(buffer)

      def for_message(obj : Message):
        {
          "stdin": self.sock_stdin_dest,
          "stdout": self.sock_stdout_dest,
          "stderr": self.sock_stderr_dest
        }[obj.tunnel].put(obj)

      basic_handlers = {
        Message: for_message
      }

      if type(decoded) in basic_handlers:
        basic_handlers[type(decoded)](decoded)
      elif type(decoded) in self.command_handlers:
        self.command_handlers[type(decoded)](decoded)
      else:
        raise ValueError("Unhandled message %r" % decoded)

    except ValueError as e:
      logging.error(e)

  def run(self):
    selector = selectors.DefaultSelector()
    sock_reader = self.sock_reader()
    sock_reader.send(None)
    sock_writer = self.sock_writer()
    sock_writer.send(None)
    selector.register(self.sock.fileno(), events=selectors.EVENT_WRITE | selectors.EVENT_READ)
    while True:
      results = selector.select()
      for event_key, event_mask in results:
        if event_mask & selectors.EVENT_READ != 0:
          sock_reader.send(self.sock.recv(4096))
        if event_mask & selectors.EVENT_WRITE != 0:
          sock_writer.send(None)


class StringBuffer:

  def __init__(self):
    self._buffer = []
    self._buffer_size = 0
    self.lock = threading.Lock()

  def read_until_from_queue(self, n, q : queue.Queue, cond : callable = None):
    if cond is None:
      cond = lambda x : True

    while n < 0 or self._buffer_size < n:
      message: Message = q.get()
      if message.eof:
        break

      self._buffer.append(message.message)
      self._buffer_size += len(message.message)
      if cond(message):
        break

  def readline_from_queue(self, q):
    with self.lock:
      self.read_until_from_queue(-1, q, lambda x : "\n" in x.message)

      result = ''
      while len(self._buffer) != 0:
        newline_index = self._buffer[0].find('\n')
        if newline_index == -1:
          result += self._buffer[0]
          self._buffer_size -= len(self._buffer[0])
          self._buffer.pop(0)
        else:
          result += self._buffer[0][0:newline_index + 1]
          if newline_index == len(self._buffer[0]) - 1:
            self._buffer.pop(0)
          else:
            self._buffer[0] = self._buffer[0][newline_index + 1:]
          self._buffer_size -= newline_index + 1
          break
      return result

  def read_from_queue(self, q, n=-1):
    with self.lock:
      self.read_until_from_queue(n, q)

      if n < 0:
        result = ''.join(self._buffer)
        self._buffer = []
        self._buffer_size = 0
      else:
        result = ''
        rest = n
        while len(self._buffer) != 0 and rest > 0:
          l = len(self._buffer[0])
          if l <= rest:
            result += self._buffer[0]
            self._buffer.pop(0)
            self._buffer_size -= l
            rest -= l
          else:
            result += self._buffer[0][0:rest]
            self._buffer[0] = self._buffer[0][rest:]
            self._buffer_size -= rest
            rest -= rest

      return result


class IOProxy:

  def __init__(self,
               input_queue : queue.Queue = None,
               output_queue : queue.Queue = None):
    self.input_queue = input_queue
    self.output_queue = output_queue

    self._buffer = StringBuffer()

  def read(self, n=-1):
    return self._buffer.read_from_queue(self.input_queue, n)

  def readline(self):
    return self._buffer.readline_from_queue(self.input_queue)

  def write(self, tunnel : str, text : str):
    self.output_queue.put(Message(eof=False, tunnel=tunnel, message=text))

class IOProxyReader(io.TextIOWrapper):

  def __init__(self, proxy : IOProxy, *args, **kwargs):
    self._proxy = proxy
    super().__init__(*args, **kwargs)

  def read(self, n=-1):
    return self._proxy.read(n)

  def readline(self, *args, **kwargs):
    return self._proxy.readline()

class IOProxyWriter(io.TextIOWrapper):

  def __init__(self, tunnel : str, proxy : IOProxy, *args, **kwargs):
    self.tunnel = tunnel
    self._proxy = proxy
    super().__init__(*args, **kwargs)

  def write(self, t : str):
    self._proxy.write(self.tunnel, t)

