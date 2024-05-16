from bs4 import BeautifulSoup
import requests
import re
import os

URL = "https://www.cnet.com/ai-atlas/"
FILE_NAME = "tracked_urls.txt"


def load_tracked_urls(filename):
    if os.path.exists(filename):
        with open(filename, "r") as file:
            return set(file.read().splitlines())
    return set()


def save_tracked_urls(filename, urls):
    with open(filename, "w") as file:
        for url in urls:
            file.write(f"{url}\n")


response = requests.get(URL)
if response.status_code == 200:
    content = response.text
    soup = BeautifulSoup(content, "html.parser")

    blog_text = []
    blog_link = []

    # Load previously tracked URLs
    tracked_urls = load_tracked_urls(FILE_NAME)

    # Find all <a> elements with class "c-storiesNeonHighlightsCard_link"
    blogs = soup.find_all("a", class_="c-storiesNeonHighlightsCard_link")

    if blogs:
        new_articles_found = False
        for blog in blogs:
            # Extract text and link
            text = blog.get_text(strip=True)
            link = blog.get('href')
            # Construct full URL
            full_link = f"https://www.cnet.com{link}"
            # Exclude empty strings and previously tracked links
            if text and link and full_link not in tracked_urls:
                # Use regex to remove time-related parts
                text = re.split(r'\d{1,2} (?:hour|hours|day|days) ago', text)[0].strip()
                text = re.split(r'\d{1,2}:\d{2} • \s*\d{1,2} (?:hour|hours|day|days) ago', text)[0].strip()
                blog_text.append(text)
                blog_link.append(full_link)
                tracked_urls.add(full_link)
                new_articles_found = True

        if new_articles_found:
            # Print new articles
            for text, link in zip(blog_text, blog_link):
                print(f"Text: {text}")
                print(f"Link: {link}")
                print()  # Add an empty line for better readability

            # Save updated URLs to the file
            save_tracked_urls(FILE_NAME, tracked_urls)
        else:
            print("Stay tuned, new news will come.")

else:
    print("Failed to retrieve the webpage.")
