import json
from typing import *

class Message(NamedTuple):
  eof : bool
  tunnel : str
  message : str

class LoadCodeByPath(NamedTuple):
  path : str
  pwd : str
  environ : dict
  argv : list

class JsonProtocol:

  sep = ord('\n')

  @staticmethod
  def obj_to_bytes(obj : dict):
    return json.dumps(obj, ensure_ascii=False).encode('utf-8') + b'\n'

  @staticmethod
  def bytes_to_obj(b : bytes) -> dict:
    return json.loads(b.decode('utf-8'), encoding='utf-8')

  @staticmethod
  def encode(obj) -> bytes:
    def for_message(obj : Message):
      return JsonProtocol.obj_to_bytes({
        "method": "msg",
        "tunnel": obj.tunnel,
        "message": obj.message,
        "eof": False
      })

    def for_load_code_by_path(obj : LoadCodeByPath):
      return JsonProtocol.obj_to_bytes({
        "method": "load_code_by_path",
        "path": obj.path,
        "pwd": obj.pwd,
        "environ": obj.environ,
        "argv": obj.argv
      })

    return {
      Message: for_message,
      LoadCodeByPath: for_load_code_by_path
    }[type(obj)](obj)

  @staticmethod
  def decode(b: bytes):
    try:
      d = JsonProtocol.bytes_to_obj(b)

      if d["method"] == "msg":
        return Message(tunnel=d["tunnel"], message=d["message"], eof=d["eof"])
      elif d["method"] == "load_code_by_path":
        return LoadCodeByPath(path=d["path"], pwd=d["pwd"], environ=d["environ"], argv=d["argv"])
      else:
        raise ValueError()

    except Exception as e:
      raise ValueError("Wrong message: %r" % b)