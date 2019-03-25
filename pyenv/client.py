import pyenv
import os

from typing import *
import queue
import socket
import threading
import sys
import argparse

class Client:

  def __init__(self, host_addr : Tuple[str, int], code_config : 'CodeConfig'):
    self.sock = socket.socket()
    self.sock.connect(host_addr)
    self.sock.setblocking(False)

    self.stdin_queue = queue.Queue()
    self.stdout_queue = queue.Queue()
    self.stderr_queue = queue.Queue()

    self.stdin_proxy = pyenv.io.IOProxy(input_queue=None, output_queue=self.stdin_queue)
    self.stdout_proxy = pyenv.io.IOProxy(input_queue=self.stdout_queue, output_queue=None)
    self.stderr_proxy = pyenv.io.IOProxy(input_queue=self.stderr_queue, output_queue=None)

    self.socket_splitter = pyenv.io.SocketSplitter(protocol=pyenv.protocol.JsonProtocol(),
                                                   sock=self.sock,
                                                   sock_write_source=self.stdin_queue,
                                                   sock_stdin_dest=None,
                                                   sock_stdout_dest=self.stdout_queue,
                                                   sock_stderr_dest=self.stderr_queue)
    
    self.code_config = code_config

  def stdin_collector(self):
    while True:
      _in = input()
      self.stdin_proxy.write("stdin", _in)

  def stdout_collector(self):
    while True:
      print(self.stdout_proxy.readline())

  def stderr_collector(self):
    while True:
      print(self.stderr_proxy.readline())
      
  def load_code(self, cfg : 'CodeConfig'):
    obj = pyenv.protocol.LoadCodeByPath(
      path=cfg.code_path,
      pwd=cfg.pwd,
      environ=cfg.environ,
      argv=cfg.argv
    )
    
    self.stdin_queue.put(obj)    

  def run(self):
    threading.Thread(target=self.socket_splitter.run).start()
    threading.Thread(target=self.stdin_collector).start()
    threading.Thread(target=self.stdout_collector).start()
    threading.Thread(target=self.stderr_collector).start()
    
    self.load_code(self.code_config)

class CodeConfig:
  
  def __init__(self, code_path, pwd=None, environ=None, argv=None):
    self.code_path = code_path
    self.pwd = os.getcwd() if pwd is None else pwd
    self.environ = os.environ
    if environ:
      self.environ.update(environ)
    self.argv = [code_path] if argv is None else argv

def main(argv):
  parser = argparse.ArgumentParser(add_help=True)
  required = parser.add_argument_group('required named arguments')
  required.add_argument('f', action='store', help='The path to your code. ')
  optionals = parser.add_argument_group('required named arguments')
  optionals.add_argument('-ip', action='store', dest='ip', default='127.0.0.1', help='IP address of the pyenv host. ')
  optionals.add_argument('-port', action='store', default='8964', help='Port of the pyenv host. ', type=int)
  optionals.add_argument('-wd', action='store', default=os.getcwd(), help='The user working directory. Note that host '
                                                                          'runs in the manner of a single process '
                                                                          'but each thread may require different '
                                                                          'working directories, this do not change '
                                                                          'the process\'s working directory, '
                                                                          'but merely records it. ')
  optionals.add_argument('-env', action='store', default=None, help='Extra environment variables for your script. ')

  optionals.add_argument('rest', nargs=argparse.REMAINDER)
  argv = parser.parse_args(argv[1:])

  client = Client((argv.ip, argv.port), CodeConfig(argv.f, pwd=argv.wd, environ=argv.env, argv=[argv.f] + argv.rest))
  client.run()

if __name__ == '__main__':
  main(sys.argv)