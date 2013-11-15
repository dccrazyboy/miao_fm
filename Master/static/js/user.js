
function edit_user_success_modal(data)
{
    // console.info(data)
    $("#editUser").empty();
    // console.info('asdasdsa')
    // console.info(data.user_level)
    var strInputText =
    '<table> \
        <tr><td><span class="input-group-addon">user_id</span></td><td><input disabled="disabled" type="text" class="form-control" value="' + data.user_id +'"></td></tr>\
        <tr><td><span class="input-group-addon">user_name</span></td><td><input disabled="disabled" type="text" class="form-control"  value="' + data.user_name +'"></td></tr>\
        <tr><td><span class="input-group-addon">user_password</span></td><td><input disabled="disabled" type="text" class="form-control"  value="' + data.user_password +'"></td></tr>\
        <tr><td><span class="input-group-addon">user_listened</span></td><td><input disabled="disabled" type="text" class="form-control"  value="' + data.user_listened +'"></td></tr>\
        <tr><td><span class="input-group-addon">user_level</span></td><td>\
        <select class="form-control">';
    user_level = new Array("normal","uploader","admin","disable");
    for (var i = 0; i < user_level.length; i++) {
        var opt = '';
        // console.info(user_level[i]);
        if (user_level[i] == data.user_level)
        {
            opt = '<option value="' + user_level[i] + '" selected="selected">' + user_level[i] + '</option>';
        }
        else
        {
            opt = '<option value="' + user_level[i] + '">' + user_level[i] + '</option>';
        }
        strInputText += opt;
    };
    strInputText += '</select></td></tr>\
        </table>';
    $("#editUser").append(strInputText);
}

function edit_user_error_modal(data)
{
    $("#editUser").empty();
    var strInputText = '<p>Sorry,the song you find does not exist!</p>';
    $("#editUser").append(strInputText);
}


function render_user_list(data)
{
    $("#addUser > tbody").empty();
    // console.info(data);
    for(var i = 0;i < data.length;++i){
        var tdstr = '<tr class="' + data[i].user_id + '"><td>'+data[i].user_id+'</td> \
            <td>'+data[i].user_name+'</td> \
            <td>' + data[i].user_password+'</td> \
            <td>'+ data[i].user_level +'</td> \
            <td><a id="' + data[i].user_id + '"" href="#myModal3" class="btn btn btn-success btn-xs" data-toggle="modal" onClick ="editUser(this)">Edit</a>&nbsp\
            <button class="btn btn-danger btn-xs" onClick ="delUser(this)">del</button></td> \
            </tr>';
        //console.info(tdstr);
        $("#addUser > tbody:last").append(tdstr);
    }
}