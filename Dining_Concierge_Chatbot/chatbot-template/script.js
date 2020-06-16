//links
//http://eloquentjavascript.net/09_regexp.html
//https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Regular_Expressions

// use 

var messages = [], //array that hold the record of each string in chat
  lastUserMessage = "", //keeps track of the most recent input string from the user
  botMessage = "", //var keeps track of what the chatbot is going to say
  botName = 'Chatbot', //name of the chatbot
  talking = true; //when false the speach function doesn't work
//
//
//****************************************************************
//****************************************************************
//****************************************************************
//****************************************************************
//****************************************************************
//****************************************************************
//****************************************************************
//edit this function to change what the chatbot say
function chatbotResponse(callback) {
    talking = true;
  botMessage = "";
  	$.ajax({
	type: "POST",
	url: 'https://c9zvptgyli.execute-api.us-east-1.amazonaws.com/beta/myresource',
	contentType: 'application/json',
	headers: {
	'Authorization' : 'AWS4-HMAC-SHA256 Credential=AKIAJDEC2A5RWBZLMVRA/20191005/us-east-1/execute-api/aws4_request,SignedHeaders=content-length;content-type;host;x-amz-date, Signature=89402a06ec7df4170ff178790e5a9bfc743701fa0604237bbee67adeccfa0e3a'},
	mode: 'cors',
	data: JSON.stringify({
		'name': lastUserMessage,
	}),
	success: function(res){
	 botMessage =  res.message;
	 console.log(res.message);
	 console.log(res["message"]);
	 callback(botMessage);

},
	error: function(){
	botMessage = "Sorry I did not get that" ;
 	console.log("failure");
 	callback(botMessage);
 }});
}
//****************************************************************
//****************************************************************
//****************************************************************
//****************************************************************
//****************************************************************
//****************************************************************
//****************************************************************
//
//
//
//this runs each time enter is pressed.
//It controls the overall input and output
function newEntry() {
  //if the message from the user isn't empty then run 
  if (document.getElementById("chatbox").value !== "") {
    //pulls the value from the chatbox ands sets it to lastUserMessage
    lastUserMessage = document.getElementById("chatbox").value;
    //sets the chat box to be clear
    document.getElementById("chatbox").value = "";
    //adds the value of the chatbox to the array messages
    messages.push(lastUserMessage);
    //Speech(lastUserMessage);  //says what the user typed outloud
    //sets the variable botMessage in response to lastUserMessage
    var apigClient = apigClientFactory.newClient();
    
    apigClient.chatbotPost({},{
        'name' : lastUserMessage
        }, {})
        .then((response) => {
        console.log('checkout api call returned', response);
        var data = response.data;
        if (data.errorMessage) {
          botMessage = 'Oops, something went wrong. Please try again.';
        }else
            botMessage = data.message;
         //add the chatbot's name and message to the array messages
      messages.push("<b>" + botName + ":</b> " + botMessage);
      // says the message using the text to speech function written below
      Speech(botMessage);
      //outputs the last few array elements of messages to html
      for (var i = 1; i < 8; i++) {
        if (messages[messages.length - i])
          document.getElementById("chatlog" + i).innerHTML = messages[messages.length - i];
    }

      })
      .catch((error) => {
        console.log('an error occurred during checkout');
        console.log(error);
      });

    // chatbotResponse(function(botMessage){
    //   //add the chatbot's name and message to the array messages
    //   messages.push("<b>" + botName + ":</b> " + botMessage);
    //   // says the message using the text to speech function written below
    //   Speech(botMessage);
    //   //outputs the last few array elements of messages to html
    //   for (var i = 1; i < 8; i++) {
    //     if (messages[messages.length - i])
    //       document.getElementById("chatlog" + i).innerHTML = messages[messages.length - i];
    // }
    // });

  }
}

//text to Speech
//https://developers.google.com/web/updates/2014/01/Web-apps-that-talk-Introduction-to-the-Speech-Synthesis-API
function Speech(say) {
  if ('speechSynthesis' in window && talking) {
    var utterance = new SpeechSynthesisUtterance(say);
    //msg.voice = voices[10]; // Note: some voices don't support altering params
    //msg.voiceURI = 'native';
    //utterance.volume = 1; // 0 to 1
    //utterance.rate = 0.1; // 0.1 to 10
    //utterance.pitch = 1; //0 to 2
    //utterance.text = 'Hello World';
    //utterance.lang = 'en-US';
    speechSynthesis.speak(utterance);
  }
}

//runs the keypress() function when a key is pressed
document.onkeypress = keyPress;
//if the key pressed is 'enter' runs the function newEntry()
function keyPress(e) {
  var x = e || window.event;
  var key = (x.keyCode || x.which);
  if (key == 13 || key == 3) {
    //runs this function when enter is pressed
    newEntry();
  }
  if (key == 38) {
    console.log('hi')
      //document.getElementById("chatbox").value = lastUserMessage;
  }
}

//clears the placeholder text ion the chatbox
//this function is set to run when the users brings focus to the chatbox, by clicking on it
function placeHolder() {
  document.getElementById("chatbox").placeholder = "";
}