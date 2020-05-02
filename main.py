from flask import Flask, render_template, redirect, url_for, session
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import textblob
import datetime
import requests
import numpy as np


def get_data ():
  url = "https://api.covid19api.com/total/country/singapore"
  response = requests.get(url)
  data_ = response.json()
  # Country, CountryCode, Province, City, CityCode, Lat, Lon, Confirmed, Deaths, Recovered, Date
  dates = np.array([])
  confirmed_cases = np.array([])
  death_cases = np.array([])
  recovered_cases = np.array([])

  for data in data_:
    date_ = data["Date"].split("T")[0].split("-")
    date = datetime.datetime(int(date_[0]), int(date_[1]), int(date_[2]))
    dates = np.append(dates, date)
    confirmed_cases = np.append(confirmed_cases, int(data["Confirmed"]))
    death_cases = np.append(death_cases, int(data["Deaths"]))
    recovered_cases = np.append(recovered_cases, int(data["Recovered"]))

  fig, ax = plt.subplots()
  ax.plot(dates, confirmed_cases, label="Confirmed Cases")
  ax.plot(dates, death_cases, label="Death Cases")
  ax.plot(dates, recovered_cases, label="Recovered Cases")
  ax.set_xlabel("Date")
  ax.set_ylabel("Number of Cases")
  ax.set_title("Covid-19 in Singapore")
  ax.xaxis.set_minor_locator(mdates.DayLocator(interval=1))
  ax.xaxis.set_major_locator(mdates.DayLocator(interval=15))
  ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
  ax.legend()
  fig.savefig("static/img/data.png")
  

def get_age (age):
  '''
  Age group:
  -Children (Age: <= 12)
  -Teens (12 < Age <= 18)
  -Young Adults (18 < Age <= 25)
  -Working Adults ( 25 < Age <= 65)
  -Seniors (Age > 65 )
  '''
  if age <= 12:return "Children"
  elif 12 < age <= 18:return "Teens"
  elif 18 < age <= 25:return "Young Adults"
  elif 25 < age <= 65:return "Working Adults"
  else:return "Seniors"


def get_category (sentiment_metric):
  '''
  Sentiment Category Sentiment_Metric (S) Range
  Very Negative S ≤ 2.5
  Slightly Negative 2.5 < S ≤ 4.5
  Neutral 4.5 < S ≤ 6.5
  Slightly Positive 6.5 < S ≤ 8.5
  Very Positive S > 8.5
  '''
  if sentiment_metric <= 2.5:return "Very Negative"
  elif 2.5 < sentiment_metric <= 4.5:return "Slightly Negative"
  elif 4.5 < sentiment_metric <= 6.5:return "Neutral"
  elif 6.5 < sentiment_metric <= 8.5:return "Positive"
  else:return "Very Positive"


def process_data (filename):
  with open (f"static/data/{filename}.csv", "r") as people_responses_file:
    people_responses = people_responses_file.readlines()

  # headers: Date_YYYYMMDD,Statement,Age,Sentiment_Metric
  people_responses = [response.rstrip() for response in people_responses]

  for i in range (1, len(people_responses)):
    temp = people_responses[i].split(",")
    date = temp[0]
    if filename != "people_responses_untagged":
      sentiment_metric = float(temp[-1])
      age = int(temp[-2])
      statement = temp[1:len(temp)-2]
    else:
      age = int(temp[-1])
      statement = temp[1:len(temp)-1]
    if filename != "people_responses_untagged":
      people_responses[i] = [date, statement[0], age, sentiment_metric]
    else:
      people_responses[i] = [date, statement[0], age]
  return people_responses

app = Flask(__name__)
app.config["SECRET_KEY"] = "984RJOLM3QD;;;.RC;W"

@app.route("/")
def index ():
  people_responses_tagged = process_data("people_responses_tagged")
  people_responses_untagged = process_data("people_responses_untagged")
  people_responses_untagged[0] = people_responses_untagged[0].split(",")

  people_responses_untagged[0].append("Sentiment_Metric")
  for i in range (1, len(people_responses_untagged)):
    # print(people_responses_untagged[i][1][0].rstrip())
    text = people_responses_untagged[i][1].rstrip()
    response = textblob.TextBlob(text)
    polarity = response.sentiment.polarity
    # -1 to 1 => 1 to 10
    # m = 4.5, c = 5.5 ; y= mx + c
    sentiment_metric = 4.5 * polarity + 5.5
    sentiment_metric = round(sentiment_metric, 2)
    people_responses_untagged[i].append(sentiment_metric)


  ### DATA PROCESSING ####

  def get_percentage_of_negative_sentiment (data):
    number_of_responses = len(data) - 1
    # negative sentiment_metric
    negative_sentiment_threshold = 5.5
    percentage_of_negative_sentiment = 0
    for i in range (1, len(data)):
      sentiment_metric = float(data[i][3])
      percentage_of_negative_sentiment += sentiment_metric <= negative_sentiment_threshold

    percentage_of_negative_sentiment = round(percentage_of_negative_sentiment/number_of_responses * 100, 2)
    return percentage_of_negative_sentiment

  def get_sentiment_by_age (data):
    number_of_responses = len(data) - 1
    # calculates and summarises the average (mean) sentiment by age groups
    sentiment_by_age = {"Children": {"population": 0, "avg_sentiment_metric": 0},
                        "Teens": {"population": 0, "avg_sentiment_metric": 0},
                        "Young Adults": {"population": 0, "avg_sentiment_metric": 0},
                        "Working Adults": {"population": 0, "avg_sentiment_metric": 0},
                        "Seniors": {"population": 0, "avg_sentiment_metric": 0}}

    for i in range (1, len(data)):
      sentiment_metric = float(data[i][3])
      age = int(data[i][2])
      sentiment_by_age[get_age(age)]["avg_sentiment_metric"] += sentiment_metric
      sentiment_by_age[get_age(age)]["population"] += 1

    for age_group in sentiment_by_age:
      if sentiment_by_age[age_group]["population"] == 0: # handle ZeroDivisionError
        continue
      sentiment_by_age[age_group]["avg_sentiment_metric"] = sentiment_by_age[age_group]["avg_sentiment_metric"]/sentiment_by_age[age_group]["population"]
      sentiment_by_age[age_group]["avg_sentiment_metric"] = round(sentiment_by_age[age_group]["avg_sentiment_metric"], 2)
    return sentiment_by_age

  def get_average_sentiment (data):
    number_of_responses = len(data) - 1
    # calculate average sentiment across users
    average_sentiment = 0
    for i in range (1, len(data)):
      sentiment_metric = float(data[i][3])
      average_sentiment += sentiment_metric

    average_sentiment /= number_of_responses
    average_sentiment = round(average_sentiment, 2)

    return average_sentiment

  def get_sentiment_by_category (data):
    number_of_responses = len(data) - 1
    sentiment_by_category = {"Very Negative": 0,
                            "Slightly Negative": 0,
                            "Neutral": 0,
                            "Positive": 0,
                            "Very Positive": 0}
    for i in range (1, len(data)):
      sentiment_metric = float(data[i][3])
      sentiment_by_category[get_category(sentiment_metric)] += 1

    for category in sentiment_by_category:
      sentiment_by_category[category] = 100 * sentiment_by_category[category] / number_of_responses
      sentiment_by_category[category] = round(sentiment_by_category[category], 2)
    return sentiment_by_category


  to_process = [people_responses_tagged, people_responses_untagged]
  for data in to_process:
    average_sentiment = get_average_sentiment(data)
    percentage_of_negative_sentiment = get_percentage_of_negative_sentiment(data)
    sentiment_by_age = get_sentiment_by_age(data)
    sentiment_by_category = get_sentiment_by_category(data)
    if data == people_responses_tagged:
      data_people_responses_tagged = {"average_sentiment": average_sentiment,
                                    "percentage_of_negative_sentiment": percentage_of_negative_sentiment,
                                    "sentiment_by_age": sentiment_by_age,
                                    "sentiment_by_category": sentiment_by_category}
    else:
      data_people_responses_untagged = {"average_sentiment": average_sentiment,
                                      "percentage_of_negative_sentiment": percentage_of_negative_sentiment,
                                      "sentiment_by_age": sentiment_by_age,
                                      "sentiment_by_category": sentiment_by_category}

  return render_template("index.html", people_responses_tagged=people_responses_tagged[1:],
                          people_responses_untagged=people_responses_untagged[1:],
                          data_people_responses_tagged=data_people_responses_tagged,
                          data_people_responses_untagged=data_people_responses_untagged)

if __name__ == "__main__":
  app.run(host="0.0.0.0", debug=True)
  # system("pkill -9 python")
