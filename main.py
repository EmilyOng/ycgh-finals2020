from flask import Flask, render_template, redirect, url_for, session
import matplotlib.pyplot as plt

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

app = Flask(__name__)
app.config["SECRET_KEY"] = "984RJOLM3QD;;;.RC;W"

@app.route("/")
def index ():
  with open ("static/data/people_responses_tagged.csv", "r") as people_responses_tagged_file:
    people_responses_tagged = people_responses_tagged_file.readlines()

  # headers: Date_YYYYMMDD,Statement,Age,Sentiment_Metric
  people_responses_tagged = [response.rstrip() for response in people_responses_tagged]
  for i in range (1, len(people_responses_tagged)):
    temp = people_responses_tagged[i].split(",")
    date = temp[0]
    sentiment_metric = float(temp[-1])
    age = int(temp[-2])
    statement = temp[1:len(temp)-2]
    people_responses_tagged[i] = [date, statement, age, sentiment_metric]

    # calculate average sentiment across users
    average_sentiment = 0
    number_of_responses = len(people_responses_tagged) - 1
    # negative sentiment_metric
    negative_sentiment_threshold = 5.5
    percentage_of_negative_sentiment = 0

    # calculates and summarises the average (mean) sentiment by age groups
    sentiment_by_age = {"Children": {"population": 0, "avg_sentiment_metric": 0},
                        "Teens": {"population": 0, "avg_sentiment_metric": 0},
                        "Young Adults": {"population": 0, "avg_sentiment_metric": 0},
                        "Working Adults": {"population": 0, "avg_sentiment_metric": 0},
                        "Seniors": {"population": 0, "avg_sentiment_metric": 0}}

    for i in range (1, len(people_responses_tagged)):
      sentiment_metric = float(people_responses_tagged[i][3])
      age = int(people_responses_tagged[i][2])
      average_sentiment += sentiment_metric
      percentage_of_negative_sentiment += sentiment_metric <= negative_sentiment_threshold
      sentiment_by_age[get_age(age)]["avg_sentiment_metric"] += sentiment_metric
      sentiment_by_age[get_age(age)]["population"] += 1

    # get the mean sentiment
    plt_age_group = []
    plt_mean_sentiment = []
    for age_group in sentiment_by_age:
      plt_age_group.append(age_group)
      if sentiment_by_age[age_group]["population"] == 0: # handle ZeroDivisionError
        plt_mean_sentiment.append(0)
        continue

      sentiment_by_age[age_group]["avg_sentiment_metric"] /= sentiment_by_age[age_group]["population"]
      sentiment_by_age[age_group]["avg_sentiment_metric"] = round(sentiment_by_age[age_group]
      ["avg_sentiment_metric"], 2)
      plt_mean_sentiment.append(sentiment_by_age[age_group]["avg_sentiment_metric"])

    average_sentiment /= number_of_responses
    average_sentiment = round(average_sentiment, 2)
    percentage_of_negative_sentiment = round(percentage_of_negative_sentiment/number_of_responses * 100, 2)

  # graph out the mean sentiment by age group
  plt.bar(plt_age_group, plt_mean_sentiment)
  plt.savefig("static/img/32-Sentiment by Age Group.png")
  plt.close()
  return render_template("index.html", people_responses_tagged=people_responses_tagged[1:],
                          data = {"average_sentiment": average_sentiment,
                                  "percentage_of_negative_sentiment": percentage_of_negative_sentiment,
                                  "sentiment_by_age": sentiment_by_age})

if __name__ == "__main__":
  app.run(host="0.0.0.0", debug=True)
  # system("pkill -9 python")
