$(document).ready(function() {
    $(".clickable-row").click(function() {
        window.location = "/domain?identifier=" + $(this).data("id");
    });
});
