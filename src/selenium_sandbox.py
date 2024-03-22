from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class SeleniumSandbox(object):
    def __init__(self):
        self.driver = webdriver.Chrome()

    def execute_code(self, code):
        print(globals())
        local_vars = {"driver":self.driver, "result": None}
        global_vars = {key: globals()[key] for key in globals() if key not in ["__name__", "__doc__", "__package__", "__loader__", "__spec__", "__annotations__", "__builtins__", "__file__", "__cached__"]}
        exec(code, global_vars, local_vars)
        return local_vars

    def post_execute(self, result):
        return result

if __name__ == "__main__":
    sandbox = SeleniumSandbox()

    a = """
driver.get("https://www.google.com")

search_box = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.NAME, "q"))
)
search_box.send_keys("obstacle")

suggestions = WebDriverWait(driver, 10).until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".erkvQe li span"))
)

result = [suggestion.text for suggestion in suggestions]
inputs = driver.find_elements(By.TAG_NAME,"input");
inputs += driver.find_elements(By.TAG_NAME,"button");
inputs += driver.find_elements(By.TAG_NAME,"a");
inputs += driver.find_elements(By.TAG_NAME,"textarea");
"""

    b = """
driver.execute_script("window.open('');")
driver.switch_to.window(driver.window_handles[-1])

# Now you can navigate to a new URL in the new tab
driver.get("https://www.google.com")
"""
    for ele in sandbox.execute_code(a)["inputs"]:
        print(ele.get_attribute('outerHTML'),ele.get_attribute('name'))

