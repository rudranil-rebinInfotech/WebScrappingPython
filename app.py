import requests
import csv
import time
import os
from flask import Flask, request, send_file
from flask_cors import CORS

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
port = 5000

email = ["rudranilbanerjee192@gmail.com", "rudranil.banerjee@rebininfotech.com"]
link_password = ["Rudranil@123", "Rudranil@12345@1999"]
i = 0


def save_html(driver, file_path):
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(driver.page_source)


def scrape_linkedin(url):
    options = Options()
    # options.add_argument("--headless")

    driver = webdriver.Chrome(options=options)

    global i
    if i == len(email) or i == len(link_password):
        i = 0

    try:
        driver.get("https://www.linkedin.com")

        username = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "session_key"))
        )
        username.send_keys("rudranil.banerjee@rebininfotech.com")

        password = driver.find_element(By.ID, "session_password")
        password.send_keys("Rudranil@12345@1999")

        signInButton = driver.find_element(By.XPATH, '//*[@type="submit"]')
        signInButton.click()

        time.sleep(5)

        driver.get(url)
        scroll_count = 30

        for i in range(scroll_count):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2.5)

        # scroll_height = driver.execute_script("return document.documentElement.scrollHeight")

        # while True:
        #   driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
        #   time.sleep(2.5)
        #   new_scroll_height = driver.execute_script("return document.documentElement.scrollHeight")
    
        #   if new_scroll_height == scroll_height:
        #     break
    
        #   scroll_height = new_scroll_height

        file_path = "output.html"
        save_html(driver, file_path)

        with open(file_path, "r", encoding="utf-8") as file:
            soup = BeautifulSoup(file, "html.parser")

        others_parent = soup.select("div.feed-shared-update-v2")

        records = []

        for item in others_parent:
            actorDiv = item.select_one("div.update-components-actor.display-flex")

            post_element = item.select_one("span.break-words")
            post = post_element.get_text(strip=True) if post_element else "No post found"

            if not actorDiv:
                actorDiv = item.select_one(
                    "div.update-components-actor.display-flex.update-components-actor--with-control-menu"
                )

            anchorDiv = actorDiv.select_one(
                "a.app-aware-link.update-components-actor__container-link.relative.display-flex.flex-grow-1"
            )
            profileLink = anchorDiv["href"]
            anchorTitleTag = anchorDiv.select_one("span.update-components-actor__title")
            userName = anchorTitleTag.select_one("span.visually-hidden").get_text(strip=True)
            actorDescriptionTag = anchorDiv.select_one(
                "span.update-components-actor__description.t-black--light.t-12.t-normal"
            )
            designation = actorDescriptionTag.select_one("span.visually-hidden").get_text(strip=True)
            actorSubDescriptionTag = anchorDiv.select_one("div.update-components-text-view.break-words")
            postUploadDay = actorSubDescriptionTag.select_one("span.visually-hidden").get_text(strip=True)
            days = "".join(filter(str.isdigit, postUploadDay))

            followers = "0"
            designationText = designation

            if "followers" in designation:
                followers = designation.replace(" followers", "")
                designationText = "None"

            record = {
                "UserName": userName,
                "User Profile Link": profileLink,
                "Designation": designationText,
                "Followers": followers,
                "Posted Days": f"{days} days ago",
                "Post": post,
            }

            records.append(record)

        output_file = "linkedin_user_details1.csv"

        with open(output_file, "w", encoding="utf-8", newline="") as csv_file:
            fieldnames = [
                "UserName",
                "User Profile Link",
                "Designation",
                "Followers",
                "Posted Days",
                "Post",
            ]
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)

        i += 1

        return output_file

    except Exception as e:
        print("An error occurred:", e)

    finally:
        driver.quit()


@app.route("/scrape", methods=["POST"])
def scrape():
    url = request.json["url"]

    output_file = scrape_linkedin(url)
    print(output_file)

    try:
        if output_file:
            return send_file(output_file, as_attachment=True, download_name='my_data.csv', mimetype='text/csv')
        else:
            return "CSV file path is invalid or not provided."
    except Exception as e:
        print("Error sending CSV file:", e)
        return "Internal Server Error", 500

    # finally:
    #     try:
    #       if output_file and os.path.exists(output_file):
    #         os.remove(output_file)
    #     except Exception as e:


if __name__ == "__main__":
    app.run(port=port, debug=True)
