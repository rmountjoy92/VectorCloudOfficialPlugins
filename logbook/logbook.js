function init_logbook() {
    $(".show-logbook-info").on('click', function(e) {
        var logbook_panel = $(this).closest('.logbook-panel');
        logbook_panel.find('.logbook-info-title').text($(this).attr('data-name'));
        logbook_panel.find('.logbook-info-code').text($(this).attr('data-info'));
        logbook_panel.find('.logbook-info-modal').modal('open');
    });
}


socket.on('connect', function() {
    socket.emit('request_logbook', {from_item: 0});
});

socket.on('logbook', function(message) {
    $.each(message, function(key, value) {
        $(".feed-rows-ul").each(function(e) {
            var vector_id = $(this).closest('.plugin-panels-container').attr('vector_id');
            if (vector_id == key){
                $(this).empty();
                $(this).append(value);
                init_logbook()
            }
        });
    });
});

$( document ).ready(function() {
    $(".logbook-info-modal").modal();
    $(".show-logbook-btn").on('click', function(e) {
        var vector_id = $(this).closest('.plugin-icons-container').attr('vector_id');
        show_panel(".logbook-panel", vector_id, $(this));
    });
    $("#logbook-refresh-btn").on('click', function(e) {
        var from_item = $("#logbook-from-item").val().parseInt();
        console.log(from_item)
        socket.emit('request_logbook', {from_item: from_item});
    });
    $("#logbook-next-page-btn").on('click', function(e) {
        var from_item = $("#logbook-from-item").val().parseInt() + 31;
        console.log(from_item)
        socket.emit('request_logbook', {from_item: from_item});
    });
    $("#logbook-prev-page-btn").on('click', function(e) {
        var from_item = $("#logbook-from-item").val().parseInt() - 31;
        console.log(from_item)
        socket.emit('request_logbook', {from_item: from_item});
    });
});