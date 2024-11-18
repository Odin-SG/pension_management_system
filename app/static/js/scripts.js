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

    // Функция для получения текущей процентной ставки по конкретному пользователю
    $('#user-id').on('input', function() {
        var userId = $(this).val();
        $.get("/set_interest_rate", { user_id: userId }, function(data) {
            if (data.current_rate !== undefined) {
                $('#current-rate').text(data.current_rate);
            } else {
                $('#current-rate').text('Нет данных');
            }
        });
    });

    // Отправка формы с подтверждением
    $('#set-interest-rate-form').on('submit', function(event) {
        event.preventDefault();
        var confirmAction = confirm("Вы уверены, что хотите изменить процентную ставку?");
        if (confirmAction) {
            this.submit();
        }
    });

    console.log("JS успешно подключен!");

        // Обновление цен акций
    function updatePrices() {
        fetch('/get_prices')
            .then(response => response.json())
            .then(data => {
                data.forEach(stock => {
                    const priceElement = document.querySelector(`#price-${stock.ticker}`);
                    if (priceElement) {
                        priceElement.textContent = new Intl.NumberFormat('ru-RU', { style: 'decimal', minimumFractionDigits: 2 }).format(stock.price);
                    }
                });
            })
            .catch(error => console.error('Ошибка при обновлении цен:', error));
    }

    setInterval(updatePrices, 1000);

    $(document).on('click', '.sell-button', function(event) {
        event.preventDefault(); // Останавливаем стандартное поведение формы
        const form = $(this).closest('form');
        const stockId = form.find('input[name="stock_id"]').val(); // Получаем ID акции
        const quantity = form.find('input[name="quantity"]').val(); // Количество акций для продажи

        if (!quantity || quantity <= 0) {
            alert('Введите корректное количество акций для продажи.');
            return;
        }

        fetch('/sell_stock', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: `stock_id=${stockId}&quantity=${quantity}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(data.message);
                loadInvestments(); // Обновляем список инвестиций
            } else {
                alert(data.message);
            }
        })
        .catch(error => {
            console.error('Ошибка:', error);
            alert('Ошибка при продаже акций. Попробуйте снова.');
        });
    });

    function loadInvestments() {
        fetch('/investments')
            .then(response => response.text())
            .then(html => {
                const newContent = $(html).find('.investments').html();
                $('.investments').html(newContent);
            })
            .catch(error => {
                console.error('Ошибка при обновлении инвестиций:', error);
            });
    }

     $('#login-form').on('submit', function(event) {
    event.preventDefault(); // Предотвращаем стандартное поведение формы

    const formData = {
        username: $('input[name="username"]').val(),
        password: $('input[name="password"]').val()
    };

    $.ajax({
        url: '/login',
        type: 'POST',
        data: JSON.stringify(formData),
        contentType: 'application/json', // Убедитесь, что тип данных указан как JSON
        success: function(response) {
            if (response.success) {
                // Если вход успешен, перенаправляем на дашборд
                window.location.href = '/dashboard';
            }
        },
        error: function(xhr) {
            const errorMessage = xhr.responseJSON ? xhr.responseJSON.message : 'Неизвестная ошибка';
            // Показываем сообщение об ошибке
            $('#login-error-message').text(errorMessage).show();
        }
    });
});

});