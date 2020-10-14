
  
  
Implementation by [HAKSOAT](https://www.twitter.com/HAKSOAT)  
  
Technology used:  
  
 - Selenium (Python)  
 - Redis (Python)  
  
Url: [Bittimi](https://bittimi.herokuapp.com)  
  

## Endpoints

  
 - https://bittimi.herokuapp.com/run  
   - Method: POST  
   - Takes json with the following must haves as keys:  
      - slug  
      - amount  
      - rec_name  
      - rec_email  
   - Other possible keys are:  
      - color -- if not provided, blue is used  
      - payment -- if not provided, bitcoin is used  
      - sender -- if not provided, Sendcash is used  
      - message -- if not provided "Send you a gift" is used  
   - Example: {"slug": "spotify-uk", "amount": 60, "payment": "Bitcoin"}  
   - Returns:  
      - This endpoint returns an ID. Since Selenium may take around 7 seconds, I believed it was best to have a worker running that process. This ID can then be used to retrieve the details.  
 - https://bittimi.herokuapp.com/pull?id=returned_id  
   - Method: GET  
   - This returns data in the format: {'amount':..., 'address':..., 'complete':...}
   - Here complete indicates if payment has been done and confirmed by Bitrefill.  
   - If it's still processing you get an empty json in the format: {}  
   - If there was something wrong with the extraction process, you get data in the format: {'error': reason}
  - https://bittimi.herokuapp.com/email  
	  - Method: POST 
	  - This method is expected to be used by Zapier to send body of an email, when Bitrefill sends in the login code.
	  - Takes in the JSON: {"message":...}

## Setting Up Zapier

You can find the link to "Make webhooks POSTs from emails that match searches on Gmail" when you visit: [https://zapier.com/apps/gmail/integrations/webhook](https://zapier.com/apps/gmail/integrations/webhook)
    
When you get find this on zapier, you should see an option to "TRY IT" or "CONTINUE". Then proceed with the following:

Choose account to link

In the “Customize Email Matching Search” section input:

> from: bitrefill or use this code

In the Find Data secion, click "TEST" so Zapier checks if it can find such emails in your inbox. 

If successful, click "CONTINUE"
       
Then move on to the POST section:

In url, input:

> [https://bittimi.herokuapp.com/email](https://bittimi.herokuapp.com/email)

In payload type, choose JSON
   
In the data section:

Type “message” into the left hand side input box and choose "Body plain" from the right hand side dropdown.
   
 Click "CONTINUE"
   
Then click "TEST & CONTINUE", to test out the endpoint.

If successful, you'll find a button to turn on the zap. 

## Installing Chrome Driver on Heroku

In order to make use of Chrome Driver on Heroku, you need the following build packs:

 - https://github.com/heroku/heroku-buildpack-chromedriver
 - https://github.com/heroku/heroku-buildpack-google-chrome

However, do push the code to Heroku first so it can add the Python build pack first and identify it as a Python application.

After adding the build packs, Heroku automatically adds the necessary environment variables needed for Chrome Driver to work as expected. **It does this the next time you push code**.

## Others

You need to set up environment variables BITREFILL_EMAIL and BITREFILL_PASSWORD.

You need to install the Redis To-Go addon as redis is used in the code.

Don't forget to scale the web and the worker when all setup is done, you can do that using the terminal command if you have Heroku CLI set up:

```term
heroku ps:scale web=1 worker=1
```
Or by:

Turning on the switch from the "Resources" section of Heroku's web interface.

