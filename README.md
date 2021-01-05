<p align="center">
  <img src="https://i.imgur.com/F1hjOA7.jpg" />
  <h1 align="center">NUS UTown TeleBot
</h1>
</p>

## Table of Contents
* [Introduction](#introduction)
* [Features](#features)
* [Technologies](#technologies)
* [Setup](#setup)
* [Team](#team)
* [Contributing](#contributing)
* [Others](#others)

### Introduction
Welcome to the NUS UTown TeleBot! This Bot aims to provide information about the shops and amenities available in the UTown Campus including their opening hours and locations! In addition, the bot is also able to share about current weather and haze conditions in UTown! Click [here](https://telegram.me/UTown_bot) to check out the bot!

### Features
The UTown bot is currently able to provide the following information:
```
1) Shop opening hours
2) Shop locations
3) Weather conditions
4) Haze conditions.
```

### Technologies
Technologies used by NUS UTown Telebot are as below:
##### Done with:
<p align="center">
  <img height="150" width="150" src="https://logos-download.com/wp-content/uploads/2016/10/Python_logo_icon.png"/>
</p>
<p align="center">
Python
</p>

##### Deployed on:
<p align="center">
  <img height="150" width="150" src="https://img.icons8.com/color/240/000000/heroku.png" />
</p>
<p align="center">
Heroku
</p>

##### Project Repository
```
https://github.com/TanHaus/NUSUTownTeleBot
```

### Setup
The following section will guide you through setting up your own NUS UTown Telebot (telegram account required).
* First, head over to [BotFather](https://t.me/BotFather) and create your own telegram bot with the /newbot command. After choosing an appropriate name and telegram handle for your bot, note down the bot token provided to you.
* Next, as this project is hosted on heroku, it would be easier to fork this repository instead of cloning it locally so as to facilitate easier automatic deploys later on in the guide. However, if you wish to clone this repository, go ahead and cd to where you wish to store the project and clone it as shown in the example below:
```
$ cd /home/user/exampleuser/projects/
$ git clone https://github.com/TanHaus/NUSUTownTeleBot.git
```
* Next, you will need to create a new application on [heroku](https://dashboard.heroku.com/).
* Within the heroku dashboard, configure either heroku git or github for automatic deploys (hence my suggestion to fork instead of cloning the repository).
* Once you are able to deploy your application, go under settings and create 2 new config variables:
```
TOKEN_UTOWN
PORT
```
The value of TOKEN_UTOWN would be the token obtained from [BotFather](https://t.me/BotFather) earlier. PORT would refer to the port that you are running the process on. Once the variables are setup, your bot should be good to go!
* If you would like to host the bot on your own VPS, you may refer to the guide [here](https://gist.github.com/tjtanjin/ce560069506e3b6f4d70e570120249ed). Note that you will still have to setup the 2 environment variables in the previous step (which is not covered in the telegram bot hosting guide).

### Team
* [Thien Tran](https://github.com/gau-nernst)
* [Dan Tran](https://github.com/picasdan9)
* [Gabriel Tan](https://github.com/gabztcr)
* [Tan Jin](https://github.com/tjtanjin)

### Contributing
If you have code to contribute to the project, open a pull request and describe clearly the changes and what they are intended to do (enhancement, bug fixes etc). Alternatively, you may simply raise bugs or suggestions by opening an issue.

### Others
For any questions regarding the implementation of the project, please create an issue as well.
