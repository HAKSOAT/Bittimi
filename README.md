

Implementation by [HAKSOAT](https://www.twitter.com/HAKSOAT)

Technology used:

 - Selenium (Python)
 - Redis (Python)

Url: [Bittimi](https://bittimi.herokuapp.com)
Endpoints:

 1. https://bittimi.herokuapp.com/run
	 2. Method: POST
	 3. Takes json with the following must haves as keys:
		 4. product_name
		 5. amount
		 6. payment
		 7. Example: {"product_name": "Spotify USA", "amount": 60, "payment": "Bitcoin"}
	 4. Other possible keys are:
		 5. color -- if not provided, blue is used
		 6. payment -- if not provided, bitcoin is used
		 7. sender -- if not provided, Sendcash is used
		 8. message -- if not provided "Send you a gift" is used
	 5. Returns:
		 6. This endpoint returns an ID. Since Selenium may take around 7 seconds, I believed it was best to have a worker running that process. This ID can then be used to retrieve the details.
 2. https://bittimi.herokuapp.com/pull?id=returned_id
	 3. Method: GET
	 4. This returns data in the format: {'amount':..., 'address':...}
	 5. If there was something wrong with the extraction process, you get data in the format: {'error': reason}


