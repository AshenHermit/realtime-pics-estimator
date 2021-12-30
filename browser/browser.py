from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from pathlib import Path
import inspect
import json
import time
from browser.script import Script
from browser.pics_estimator_script import PicsEstimatorScript
import traceback
from selenium.common.exceptions import NoSuchWindowException

CWD = Path(__file__).parent.resolve()

class ScriptedWindow():
    def __init__(self, browser, window_handle) -> None:
        self.browser:ScriptedBrowser = browser
        self.window_handle = window_handle
        self.scripts_by_id:dict[Script]={}

    def add_script(self, script:Script):
        if script._id not in self.scripts_by_id:
            self.scripts_by_id[script._id] = script
            script._driver = self.browser.driver
            self.execute_script(script)
            print(f"added script {script}")

    def execute_script(self, script:Script):
        message = self.browser.execute_script(self, script._render_js_script())
        script._process_returned_message(message)

    def update_scripts(self):
        for script in self.scripts_by_id.values():
            self.execute_script(script)

    def update(self):
        self.update_scripts()

class ScriptedBrowser():
    def __init__(self) -> None:
        self.driver = self.make_driver()
        self.scripted_window:ScriptedWindow = None

    def make_driver(self) -> Chrome:
        options = Options()
        options.add_experimental_option("debuggerAddress", "localhost:9222")
        driver = Chrome(options=options)
        return driver

    def open_new_tab(self):
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.driver.execute_script('''window.open("about:blank", "_blank");''')
        self.driver.switch_to.window(self.driver.window_handles[-1])

    def reopen_window(self, window:ScriptedWindow):
        self.open_new_tab()
        window.window_handle = self.driver.current_window_handle

    def add_scripted_window(self):
        self.open_new_tab()
        window = ScriptedWindow(self, self.driver.current_window_handle)
        self.scripted_window = window
        return window

    def run(self):
        while True:
            self.update()
            time.sleep(0.1)

    def execute_script(self, window:ScriptedWindow, script_text:str):
        if self.driver.current_window_handle != window.window_handle:
            self.driver.switch_to.window(window.window_handle)
        try:
            result = self.driver.execute_script(script_text)
        except:
            traceback.print_exc()
            result = None
        return result

    def update(self):
        try:
            self.scripted_window.update()
        except NoSuchWindowException:
            self.reopen_window(self.scripted_window)

def main():
    browser = ScriptedBrowser()
    script = PicsEstimatorScript()
    window = browser.add_scripted_window()
    window.add_script(script)
    browser.run()

if __name__ == '__main__':
    main()