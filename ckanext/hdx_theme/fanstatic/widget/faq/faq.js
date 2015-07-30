function showFaqWidget(id) {
    $(id).show();



    function _triggerInputDataClass($this){
        if ($this.val() === "")
            $this.removeClass("input-content");
        else
            $this.addClass("input-content");
    }

    $(id).find('input[type="password"], input[type="text"], textarea').each(
        function(idx, el){
            _triggerInputDataClass($(el));
        }
    );
    $(id).find('input[type="password"], input[type="text"], textarea').change(
        function(){
            var $this = $(this);
            _triggerInputDataClass($this);
        }
    );
    $(id).find('input[type="password"], input[type="text"], textarea').on("keyup",
        function(){
            var $this = $(this);
            _triggerInputDataClass($this);
        }
    );

    $(id).find('input[type="submit"]').on("click", function(){
        var result = precheckForm(id);
        return !result;
    });

    function precheckForm(id){
        var error = false;
        $(id).find("input.required, textarea.required, select.required").each(function(idx, el){
            var $el = $(el);
            if ($el.is(":visible") && ($el.val() === null || $el.val() === "")){
                $el.addClass("error");
                error = true;
            } else {
                $el.removeClass("error");
            }
        });
        return error;
    }


    return false;
}

$(document).ready(function(){
    $('#topics-selector').select2();
});