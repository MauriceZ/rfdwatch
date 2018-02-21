# RFDWATCH
Tiny RedFlagDeals scraper to watch hot deals forum for specific keywords.

Start by setting up your database
```
python3 rfdwatch.py setupdb 
# by default, the db will be setup in the repo's directory.
# Use --path [path] to specify a path
```

Run with 
```
python3 rfdwatch.py watch [email] [space delimited keyword list]
```
This tool is meant to be wrapped as a cron job.

Requires a SendGrid API key to send emails for alerts, which should be passed through the environment variable `SENDGRID_API_KEY`.
