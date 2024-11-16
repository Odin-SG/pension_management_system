$(document).ready(function() {
    var editModal = $('#edit-user-modal');
    var closeButton = $('.close-button');
    var contributeModal = $('#contribute-modal');
    var withdrawModal = $('#withdraw-modal');
    var contributeButton = $('#contribute-button');
    var withdrawButton = $('#withdraw-button');
    var withdrawCloseButton = $('.withdraw-close-button');

    $('.edit-user-button').on('click', function() {
        var userId = $(this).data('user-id');
        $('#edit-user-id').val(userId);
        editModal.show();
    });

    closeButton.on('click', function() {
        editModal.hide();
    });

    $(window).on('click', function(event) {
        if ($(event.target).is(editModal)) {
            editModal.hide();
        }
    });

    // Получение информации о конкретном пользователе
    $('.view-user-button').on('click', function() {
        var userId = $(this).data('user-id');
        $.get("/admin_panel", { user_id: userId }, function(data) {
            if (data.specific_user) {
                $('#user-details').show();
                $('#user-username').text(data.specific_user.username);
                $('#user-role').text(data.specific_user.role);
                $('#user-total-amount').text(data.specific_user.total_amount);

                var historyHtml = '';
                data.user_history.forEach(function(entry) {
                    historyHtml += '<li>Сумма: ' + entry.amount + ' руб., Дата: ' + entry.contribution_date + '</li>';
                });
                $('#user-history').html(historyHtml);
            }
        });
    });

    contributeButton.on('click', function() {
        contributeModal.show();
    });

    withdrawButton.on('click', function() {
        withdrawModal.show();
    });

    closeButton.on('click', function() {
        contributeModal.hide();
    });

    withdrawCloseButton.on('click', function() {
        withdrawModal.hide();
    });

    $(window).on('click', function(event) {
        if ($(event.target).is(contributeModal)) {
            contributeModal.hide();
        }
        if ($(event.target).is(withdrawModal)) {
            withdrawModal.hide();
        }
    });

    var userDetailsModal = $('#user-details-modal');
    var closeDetailsButton = $('.details-close-button');

    $('.view-user-button').on('click', function() {
        var userId = $(this).data('user-id');
        $.get("/admin_panel", { user_id: userId }, function(data) {
            if (data.specific_user) {
                $('#modal-user-username').text(data.specific_user.username);
                $('#modal-user-role').text(data.specific_user.role);
                $('#modal-user-total-amount').text(
                    new Intl.NumberFormat('ru-RU', { style: 'decimal', minimumFractionDigits: 2 }).format(data.specific_user.total_amount)
                );

                var historyHtml = '';
                data.user_history.forEach(function(entry) {
                    historyHtml += '<li>Сумма: ' + new Intl.NumberFormat('ru-RU', { style: 'decimal', minimumFractionDigits: 2 }).format(entry.amount) + ' руб., Дата: ' + entry.contribution_date + '</li>';
                });
                $('#modal-user-history').html(historyHtml);

                userDetailsModal.show();
            }
        });
    });

    closeDetailsButton.on('click', function() {
        userDetailsModal.hide();
    });

    $(window).on('click', function(event) {
        if ($(event.target).is(userDetailsModal)) {
            userDetailsModal.hide();
        }
    });

    // Асинхронное редактирование пользователя
    $('#edit-user-form').on('submit', function(event) {
        event.preventDefault(); // Останавливаем стандартное поведение формы

        var formData = {
            user_id: $('#edit-user-id').val(),
            new_username: $('#new-username').val(),
            new_role: $('#new-role').val(),
            new_amount: $('#new-amount').val()
        };

        fetch('/admin_panel', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Пользователь успешно обновлён!');
                $('#edit-user-modal').hide();
                location.reload(); // Обновляем таблицу
            } else {
                alert('Ошибка при обновлении пользователя: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Ошибка:', error);
        });
    });
});