

Implementation by [HAKSOAT](https://www.twitter.com/HAKSOAT)

Technology used:

 - Selenium (Python)
 - Redis (Python)

Url: [Bittimi](https://bittimi.herokuapp.com)

Endpoints:

 - https://bittimi.herokuapp.com/run
	 - Method: POST
	 - Takes json with the following must haves as keys:
		 - slug -- Note: This is case sensitive
		 - amount
	 - Other possible keys are:
		 - color -- if not provided, blue is used
		 - payment -- if not provided, bitcoin is used
		 - sender -- if not provided, Sendcash is used
		 - message -- if not provided "Send you a gift" is used
     - Example: {"slug": "Spotify USA", "amount": 60, "payment": "Bitcoin"}
	 - Returns:
		 - This endpoint returns an ID. Since Selenium may take around 7 seconds, I believed it was best to have a worker running that process. This ID can then be used to retrieve the details.
 - https://bittimi.herokuapp.com/pull?id=returned_id
	 - Method: GET
	 - This returns data in the format: {'amount':..., 'address':...}
	 - If it's still processing you get an empty json in the format: {}
	 - If there was something wrong with the extraction process, you get data in the format: {'error': reason}


