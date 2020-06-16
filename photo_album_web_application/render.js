var data = {
  "images": [{
    "bannerImg1": "https://s3.us-east-2.amazonaws.com/chatbothw1/ncik_gupta1.jpg"
  },
  {"bannerImg1" : "https://s3.us-east-2.amazonaws.com/chatbothw1/nick_gupta2.jpeg"
},
{"bannerImg1" : "https://s3.us-east-2.amazonaws.com/chatbothw1/nick_gupta3.jpeg"
}]
};


document.getElementById("displaytext").style.display = "none";

function searchPhoto()
{

  var apigClient = apigClientFactory.newClient({
                     apiKey: "swsfM8p6i71jP3kgUEwyB3DzE8xOQSjR6YCRsCXo"
        });

    var user_message = document.getElementById('note-textarea').value;

    var body = { };
    var params = {Key1 : user_message};
    var additionalParams = {};

    apigClient.searchGet(params, body , additionalParams).then(function(res){
        var data = {}
        var data_array = []
        resp_data  = res.data
        resp_data.forEach(function(obj) {var json = {};
                  json["bannerImg1"] = obj["imageUrl"];
                 data_array.push(json) }
                );

        data["images"] = data_array;
        console.log(data);

        data.images.forEach( function(obj) {
            var img = new Image();
            img.src = obj.bannerImg1;
            img.setAttribute("class", "banner-img");
            img.setAttribute("alt", "effy");
            document.getElementById("img-container").appendChild(img);
            document.getElementById("displaytext").style.display = "block";
          });
      }).catch( function(result){

      });



}

function uploadPhoto()
{
   var file_data = $("#file_path").prop("files")[0];   // Getting the properties of file from file field
	 var form_data = new FormData();                  // Creating object of FormData class
	 form_data.append("file", file_data)

   var apigClient = apigClientFactory.newClient({
                     apiKey: "swsfM8p6i71jP3kgUEwyB3DzE8xOQSjR6YCRsCXo"
        });

   var data = document.getElementById('file_path').value;
   var x = data.split("\\")
   var filename = x[x.length-1]
   console.log(filename)

   var body = {};
   var params = {"key" : filename , "bucket" : "photo-file" , "Content-Type" : "image/jpg"};
   var additionalParams = {};
  
   apigClient.uploadBucketKeyPut(params, body , additionalParams).then(function(res){
     console.log(res)
   }).catch( function(result){

   });
return false;

}
