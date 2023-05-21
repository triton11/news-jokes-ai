import boto3
import datetime
import requests
from bs4 import BeautifulSoup
import os
import openai

html_template_open = "<html><head><title>News Jokes AI</title></head><body>"
html_template_close = "</body></html>"

openai.organization = os.getenv("ORG_KEY")
openai.api_key = os.getenv("OPENAI_API_KEY")

def upload_news_to_s3(joke_data_list):
  print("Uploading to S3...")
  s3 = boto3.resource("s3")
  my_bucket = s3.Bucket('news-jokes-ai')
  date = datetime.datetime.now().strftime("%Y-%m-%d")
  html_body = ""
  
  for joke_data in joke_data_list:
    html_body += "<div>"
    html_body += "<h2> %s </h2>" % joke_data[0]
    html_body += "<p> %s </p>" % joke_data[2]
    html_body += "<p> Source: <a href=%s>AP News</a></p>" % joke_data[1]
    html_body += "</div>"

  html_heading = "<h1>Jokes for %s </h1>" % date
  html_object = html_template_open + html_heading + html_body + html_template_close
  html_file_name = date + ".html"
  my_bucket.put_object(Key=html_file_name, Body=html_object, ContentType="text/html")
  return "Success!"


def get_joke(article):
  prompt = "Write a short joke about the following news article:"
  prompt += article
  prompt += "\nJoke:"
  completion = openai.ChatCompletion.create(
    model="gpt-4",
    temperature=0.3,
    max_tokens=200,
    messages=[
      {"role": "system", "content": "You are the punniest person on the planet."},
      {"role": "user", "content": prompt}
    ]
  )
  return completion.choices[0].message.content


def scrape_news_and_create_jokes():
  URL = "https://apnews.com/"
  page = requests.get(URL)

  soup = BeautifulSoup(page.content, "html.parser")
  results = soup.find("div", class_="TopStories")
  top_stories = results.find_all("a", {"data-key": "card-headline"})
  minor_stories = results.find_all("a", {"data-key": "related-story-link"})

  # I found a lot of duplicates, so I decided to eliminate those by 
  # converting the array to a set
  headline_elements = set(
    ["https://apnews.com" + headline['href'].strip() for headline in (top_stories + minor_stories)]
  )
  
  joke_data_list = []

  for headline_url in headline_elements:
    headline_page = requests.get(headline_url)
    article_soup = BeautifulSoup(headline_page.content, "html.parser")
    article_headline = article_soup.find("h1").text
    article_body = article_soup.find("div", class_="Article")
    article_text = article_body.find_all("p")
    short_article_text = ""
    for paragraph in article_text[0:10]:
      short_article_text += paragraph.text
    
    joke_data_list.append([
      article_headline, 
      headline_url,
      get_joke(short_article_text)
    ])
  
  return joke_data_list

def lambda_handler(event, context):
  joke_data_list = [["Headline", "Joke", "https://apnews.com/"]]
  joke_data_list = scrape_news_and_create_jokes()
  upload_reply = upload_news_to_s3(joke_data_list)
  return upload_reply