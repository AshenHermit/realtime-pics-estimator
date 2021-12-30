from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from pathlib import Path
import inspect
import json
import time
import traceback

from selenium.webdriver.chrome.webdriver import WebDriver

CWD = Path(__file__).parent.resolve()

def script_reg(cls):
    if getattr(cls, "js_accessable_methods", None) is None:
        cls.js_accessable_methods = set()
    for method_name, method in cls.__dict__.items():
        if not inspect.isfunction(method): continue
        if hasattr(method, "js_accessable"):
            cls.js_accessable_methods.add(method_name)
    return cls

def js_accessable(method):
    method.js_accessable = True
    return method

class JSScriptNamespace():
    def __init__(self, script) -> None:
        self.__script:Script = script

    def __getattr__(self, name:str):
        if name=="__script" or name=="__call_js_method": raise AttributeError()
        return lambda *args: self.__call_js_method(name, *args)
    
    def __call_js_method(self, method_name:str, *args):
        self.__script._call_js(method_name, *args)

class OptFileReader():
    def __init__(self, filepath:Path) -> None:
        self.filepath = filepath
        if not self.filepath.exists():
            raise FileNotFoundError()

    def __getattr__(self, name):
        if name == "filepath": raise AttributeError()
        return getattr(self.filepath, name)

    def __read_file(self):
        self._text = self.filepath.read_text()
        self._read_time = self.filepath.stat().st_mtime
    
    @property
    def __need_to_read_file(self):
        if getattr(self, "_text", None) is None: return True
        if getattr(self, "_read_time", None) is not None:
            if self.filepath.stat().st_mtime > self._read_time:
                print(f"\"{self.filepath.name}\" changed")
                return True
        else:
            return True
        return False
    
    @property
    def text(self):
        if self.__need_to_read_file:
            self.__read_file()
        return self._text
            

@script_reg
class Script():
    def __init__(self, id:str="script", javascript_file:Path=None, script_class_name="Script", script_base_file:Path=None, driver:WebDriver=None) -> None:
        self._id = id
        self._script_class_name = script_class_name
        self._script_file = OptFileReader(javascript_file)
        self._script_base_file = OptFileReader(script_base_file or CWD/"js/scriptBase.js")
        self.__calls_results = []
        self.__method_call_queue = []
        self._driver:WebDriver = driver

        self.js = JSScriptNamespace(self)
    
    def __new__(cls):
        return super().__new__(cls)

    def __str__(self):
        return f"<{self.__class__.__name__} id: \"{self._id}\", script: \"{self._script_file.name}\">"

    @property
    def _message_to_js(self):
        data = {
            "calls_results": self.__calls_results,
            "method_call_queue": self.__method_call_queue
        }
        message = json.dumps(data, ensure_ascii=False)
        return message

    @property
    def _has_something_to_send(self):
        return len(self.__calls_results)>0 or len(self.__method_call_queue)>0

    def _render_js_script(self):
        script = self._script_base_file.text
        script += "\n"
        script += self._script_file.text
        script += "\n"
        
        prototype = self._script_class_name+".prototype"
        script += prototype+".py = {};"
        script += prototype+f".$id = '{self._id}';"

        for cls in [self.__class__]:
            if getattr(cls, "js_accessable_methods", None) is None: continue
            for method_name in cls.js_accessable_methods:
                script += prototype+".py['"+method_name+"']=(async function(...args){return await this.$script.$callPython('"+method_name+"', ...args)});"

        script += "var $label='[Scripted]'; if(document.title.substring(0, $label.length)!=$label){document.title='[Scripted] '+document.title;};"

        script_getter = f"window['$script__{self._id}']"
        script += f"if(!{script_getter})"+"{"
        script += f"var script = new {self._script_class_name}();"
        script += f"{script_getter} = script;"
        script += "}"
        script += f"{script_getter}.$giveData({self._take_data()});"
        script += f"return {script_getter}.$takeData();"
        return script

    def _take_data(self):
        message = self._message_to_js
        self.__calls_results.clear()
        self.__method_call_queue.clear()
        return message

    def _process_returned_message(self, message):
        if message is None: return
        data = json.loads(message)
        method_call_queue = data.get("method_call_queue", [])
        for method_call in method_call_queue:
            method_name:str = method_call.get("method_name", "")
            call_uid:str = method_call.get("call_uid", -1)
            args:list = method_call.get("args", [])
            args = tuple(args)
            method = getattr(self, method_name, None)
            if method is not None:
                try:
                    result = method(*args)
                except:
                    traceback.print_exc()
                    result=None
                try:
                    json_text = json.dumps(result, ensure_ascii=False)
                except:
                    result = str(result)
                self.__calls_results.append({"call_uid": call_uid, "value": result})

    def _call_js(self, method_name:str, *args):
        call = {"method_name": method_name, "args": list(args)}
        self.__method_call_queue.append(call)

    @js_accessable
    def print(self, *args):
        print(*args)