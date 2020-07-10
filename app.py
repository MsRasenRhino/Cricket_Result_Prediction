import os
from flask import Flask, render_template, redirect, url_for, request
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, IntegerField, SubmitField
from wtforms.validators import DataRequired
import pandas as pd
from sklearn.linear_model import LogisticRegression
dataset=pd.read_csv('ipl.csv',index_col=0)
dataset = dataset.drop(columns=['gender', 'match_type','date','umpire_1','umpire_2','player of the match','win_by_runs','win_by_wickets'])
dataset['city'].fillna(dataset['city'].mode()[0], inplace=True)
dataset.columns[dataset.isnull().any()]

# dataset.replace(['Mumbai Indians','Kolkata Knight Riders','Royal Challengers Bangalore','Deccan Chargers','Chennai Super Kings',
#                  'Rajasthan Royals','Delhi Daredevils','Gujarat Lions','Kings XI Punjab',
#                  'Sunrisers Hyderabad','Rising Pune Supergiants','Kochi Tuskers Kerala','Pune Warriors','Rising Pune Supergiant']
#                 ,['MI','KKR','RCB','DC','CSK','RR','DD','GL','KXIP','SRH','RPS','KTK','PW','RPS'],inplace=True)


team_list=list(set(dataset['team 1'].unique()).union(set(dataset['team 2'].unique())))
venue_list=dataset.venue.unique()
tossdec_list=dataset.toss_decision.unique()
citylist=dataset.city.unique()
# print(team_list)
# print(venue_list)
# print(tossdec)
def createDict(series) :
    
    dictionary={}
    i=0
    for ser in series :
        if(ser in dictionary) :
            continue
        dictionary[ser]=i
        i=i+1
    return dictionary
teamDict=createDict(dataset['team 1'])
cityDict=createDict(dataset['city'])
venueDict=createDict(dataset['venue'])
tossDecisionDict=createDict(dataset['toss_decision'])
winnerDict=dict(teamDict)
winnerDict['tie']=14
winnerDict['no result']=15
encode = {
'team 1': teamDict,
'team 2': teamDict,
'toss_winner': teamDict,
'winner': winnerDict,
'city':cityDict,
'venue':venueDict,
'toss_decision': tossDecisionDict    
 }
dataset.replace(encode, inplace=True)
def buildModel(dataset,team1,team2) :
    dataset=dataset[
        ((dataset['team 1']==team1)&(dataset['team 2']==team2) | 
         (dataset['team 1']==team2)&(dataset['team 2']==team1))
    ]
    winner = dataset['winner']
    features = dataset.drop('winner',axis=1)
    features = pd.get_dummies(features)
    clf=LogisticRegression()
    clf.fit(features,winner)
    return clf
def pred(city,team1,team2,team1_batting_avg,team1_bowling_avg,team2_batting_avg,team2_bowling_avg,toss_decision,toss_winner,venue) :

    predictionSet = pd.DataFrame({
        'city':cityDict[city],
        'team 1':teamDict[team1],
        'team 2':teamDict[team2],
        'team_1_batting_average':team1_batting_avg,
        'team_1_bowling_average':team1_bowling_avg,
        'team_2_batting_average':team2_batting_avg,
        'team_2_bowling_average':team2_bowling_avg,
        'toss_decision':[toss_decision],
        'toss_winner':teamDict[toss_winner],
        'venue':venueDict[venue]
    })

    predictionSet = pd.get_dummies(predictionSet)
    
    clf=buildModel(dataset,teamDict[team1],teamDict[team2])
    
    prediction=clf.predict(predictionSet)
    
    for key,value in teamDict.items() :
        
        if(value==prediction) :
            
            return key
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hello its me'

# create app instance
app = Flask(__name__)
app.config.from_object(Config)
class PreForm(FlaskForm):
    team1 = SelectField('team_1', validators=[DataRequired()])
    team2 = SelectField('team_2', validators=[DataRequired()])
    submit = SubmitField('Submit', validators=[DataRequired()])
class PredictionForm(FlaskForm):
	city_match=SelectField('City', validators=[DataRequired()])
	t1_bat_avg = IntegerField('team1_batting_avg', validators=[DataRequired()])
	t1_bowl_avg = IntegerField('team1_bowling_avg', validators=[DataRequired()])
	t2_bat_avg = IntegerField('team2_batting_avg', validators=[DataRequired()])
	t2_bowl_avg = IntegerField('team2_bowling_avg', validators=[DataRequired()])
	toss_dec=SelectField('toss_decision', validators=[DataRequired()])
	toss_win=SelectField('toss_winner', validators=[DataRequired()])
	venue = SelectField('Venue', validators=[DataRequired()])
	submit = SubmitField('Submit', validators=[DataRequired()])
# routes
@app.route('/', methods=['GET', 'POST'])
def home():
    form = PreForm()
    form.team1.choices = [(team) for team in team_list]
    form.team2.choices = [(team) for team in team_list]
    if form.is_submitted():
        print(form.errors)
        return redirect(url_for('predict', 
                 team1=form.team1.data, team2=form.team2.data))
    # TODO : validations
    # if form.validate_on_submit():
    #     print(form.season.data)
    #     print(form.team1.data + form.team2.data)
    #     return redirect(url_for('predict', 
    #             season=form.season.data, team1=form.team1.data, team2=form.team2.data))
    return render_template('home.html', form=form, teams=team_list)
@app.route('/predict/<team1>_<team2>', methods=['GET', 'POST'])
def predict(team1, team2):
    form = PredictionForm()
    # form.batsman.choices = [(player) for player in players]
    # form.batsman_ns.choices = [(player) for player in players]
    # form.bowler.choices = [(player) for player in players]
    # TODO: validations
    form.city_match.choices=[(cities) for cities in citylist]
    form.toss_dec.choices=[(dec) for dec in tossdec_list]
    form.toss_win.choices=[team1,team2]
    form.venue.choices=[(place) for place in venue_list]
    if form.is_submitted():
        predictions=pred(form.city_match.data,team1,team2,form.t1_bat_avg.data,form.t1_bowl_avg.data,form.t2_bat_avg.data,form.t2_bowl_avg.data,form.toss_dec.data,form.toss_win.data,form.venue.data)

        return render_template('predict.html', 
                form=form, team1=team1, team2=team2,predictions=predictions)
    return render_template('predict.html', form=form,team1=team1, team2=team2)

# pred('Delhi','DD','RR',5.0,21.000000,5.0,5.0,'bat','RR','Feroz Shah Kotla')
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050, debug=False)






