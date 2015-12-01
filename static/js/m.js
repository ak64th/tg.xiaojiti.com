$(function(){
    $('.allow-edit-body').click(function(){
        console.log(this,$(this).data('obj'));
        var obj=$(this).data('obj');
        if(obj) {
            eval('obj='+obj+';');
        }else{
            obj=$(this)
        }
        var x=prompt('',obj.html());
        if(x){
            obj.html(x);
        }
    })
})
