import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

options = webdriver.ChromeOptions()
options.add_argument("--headless")

options.page_load_stategy = "none"

driver = Chrome(options=options)

driver.implicitly_wait(5)

url = "https://feelthemusi.com/playlist/h8nsjf"

driver.get(url)
time.sleep(20)

soup = BeautifulSoup(driver.page_source, 'html.parser')
driver.quit()


div = soup.find('div', id="playlist_content")

trackList = div.find_all('a', href=True)

for element in trackList: 
    print(element['href'])
print(len(trackList))
#print(soup.prettify())

#content = driver.find_element(By.CSS_SELECTOR, "div[class*='playlist_content'")

#print(dir(driver))
