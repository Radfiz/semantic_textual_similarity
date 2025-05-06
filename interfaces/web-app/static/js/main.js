// static/js/main.js
$(document).ready(function() {
    // Обработка формы одиночной обработки
    $('#singleForm').submit(function(e) {
        e.preventDefault();

        // Показываем индикатор загрузки
        $('#result').hide();
        $('#singleForm button').prop('disabled', true).html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Обработка...');

        // Отправка AJAX запроса
        $.ajax({
            url: '/process',
            type: 'POST',
            data: $(this).serialize(),
            success: function(response) {
                // Восстанавливаем кнопку
                $('#singleForm button').prop('disabled', false).text('Обработать');

                if (response.status === 'success') {
                    // Показываем результат
                    $('#result').show();
                    $('#result_content').text(response.result);
                } else {
                    // Показываем ошибку
                    alert('Ошибка: ' + response.message);
                }
            },
            error: function() {
                // Восстанавливаем кнопку
                $('#singleForm button').prop('disabled', false).text('Обработать');
                alert('Произошла ошибка при обработке запроса.');
            }
        });
    });

    // Обработка формы пакетной обработки
    $('#batchForm').submit(function(e) {
        e.preventDefault();

        // Скрываем предыдущие результаты и сообщения
        $('#column_selector').hide();
        $('#batch_result').hide();

        // Показываем индикатор загрузки
        $('#batch_progress').show();
        $('#batchForm button').prop('disabled', true);

        // Создаем объект FormData для отправки файла
        var formData = new FormData(this);

        // Отправка AJAX запроса
        $.ajax({
            url: '/batch',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                // Скрываем индикатор загрузки
                $('#batch_progress').hide();
                $('#batchForm button').prop('disabled', false);

                if (response.status === 'success') {
                    // Показываем результат
                    $('#batch_result_message').text('Файл успешно обработан. Обработано строк: ' + response.rows_processed);
                    $('#download_link').attr('href', response.download_url);
                    $('#batch_result').show();
                } else if (response.columns && response.message.includes('не найдена')) {
                    // Если колонка не найдена, показываем селектор колонок
                    $('#available_columns').empty();
                    response.columns.forEach(function(column) {
                        $('#available_columns').append($('<option></option>').val(column).text(column));
                    });
                    $('#column_selector').show();
                } else {
                    // Показываем ошибку
                    alert('Ошибка: ' + response.message);
                }
            },
            error: function() {
                // Скрываем индикатор загрузки
                $('#batch_progress').hide();
                $('#batchForm button').prop('disabled', false);

                alert('Произошла ошибка при обработке запроса.');
            }
        });
    });

    // Обработка выбора колонки из списка доступных
    $('#use_selected_column').click(function() {
        var selectedColumn = $('#available_columns').val();
        if (selectedColumn) {
            $('#text_column').val(selectedColumn);
            $('#column_selector').hide();
            $('#batchForm').submit();
        }
    });

    // Предпросмотр файла при его выборе
    $('#file').change(function() {
        // Скрываем предыдущие результаты и сообщения
        $('#file_preview').hide();
        $('#batch_result').hide();

        if (this.files && this.files[0]) {
            var file = this.files[0];

            // Проверка формата файла
            var validExtensions = ['.csv', '.xlsx', '.xls'];
            var fileName = file.name;
            var fileExtension = fileName.substring(fileName.lastIndexOf('.')).toLowerCase();

            if (!validExtensions.includes(fileExtension)) {
                alert('Поддерживаются только CSV и Excel файлы');
                return;
            }

            // Показываем индикатор загрузки
            $('#batch_progress').show();
            $('#batch_progress .alert').html('<div class="d-flex align-items-center"><strong>Загрузка файла...</strong><div class="spinner-border ms-auto" role="status" aria-hidden="true"></div></div>');

            // Создаем объект FormData для отправки файла
            var formData = new FormData();
            formData.append('file', file);

            // Отправка AJAX запроса для предпросмотра
            $.ajax({
                url: '/preview',
                type: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                success: function(response) {
                    // Скрываем индикатор загрузки
                    $('#batch_progress').hide();

                    if (response.status === 'success') {
                        // Заполняем предпросмотр
                        $('#preview_content').html(response.preview);
                        $('#preview_rows_count').text('Показано строк: ' + response.rows_count);

                        // Заполняем бейджи с доступными колонками
                        var badgesHtml = '';
                        response.columns.forEach(function(column) {
                            badgesHtml += '<span class="badge bg-secondary me-1 column-badge" style="cursor: pointer;" data-column="' + column + '">' + column + '</span>';
                        });
                        $('#available_cols_badges').html(badgesHtml);

                        // Показываем предпросмотр
                        $('#file_preview').show();

                        // Если есть колонка 'text', выбираем её по умолчанию
                        if (response.columns.includes('text')) {
                            $('#text_column').val('text');
                        }
                    } else {
                        alert('Ошибка: ' + response.message);
                    }
                },
                error: function() {
                    $('#batch_progress').hide();
                    alert('Произошла ошибка при загрузке файла.');
                }
            });
        }
    });

    // Выбор колонки по клику на бейдж
    $(document).on('click', '.column-badge', function() {
        var column = $(this).data('column');
        $('#text_column').val(column);

        // Выделяем выбранную колонку
        $('.column-badge').removeClass('bg-primary').addClass('bg-secondary');
        $(this).removeClass('bg-secondary').addClass('bg-primary');
    });
});