//全局ajax拦截
$(function(){
    // 设置jQuery Ajax全局的参数
    $.ajaxSetup({
        type: "POST",
        error: function(jqXHR, textStatus, errorThrown){
            switch (jqXHR.status){
                case(599):
                    window.location.href = jqXHR.getResponseHeader('location')
                    break;
                case (302):
                    window.location.href = jqXHR.getResponseHeader('location')
                    break;
                default:
                    alert("未知错误");
            }
        }
    });
});