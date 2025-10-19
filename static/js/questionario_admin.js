(function($) {
    // Função que mostra ou esconde o bloco de "Opções"
    function toggleOptions(row) {
        const $row = $(row);
        const selectElement = $row.find('.field-tipo_resposta select');
        const optionsBlock = $row.find('.inline-group');

        if (!selectElement.length || !optionsBlock.length) return; // Sai se não encontrar

        const selectedType = selectElement.val();
        const typesWithOptions = ['UNICA_ESCOLHA', 'MULTIPLA_ESCOLHA'];

        if (typesWithOptions.includes(selectedType)) {
            optionsBlock.slideDown();
        } else {
            optionsBlock.slideUp();
        }
    }

    // Função para adicionar placeholder
    function addPlaceholder(row) {
        const $row = $(row);
        const questionInput = $row.find('.field-texto_pergunta input[type="text"]');
        if (questionInput.length > 0 && !questionInput.attr('placeholder')) {
            questionInput.attr('placeholder', 'Pergunta');
        }
    }

    $(document).ready(function() {
        // Renomeia os botões
        setInterval(function() { /* ... (código existente mantido) ... */ }, 500);

        // Ouve a mudança no dropdown
        $('body').on('change', '#perguntas-group .field-tipo_resposta select', function() {
            const row = $(this).closest('.inline-related');
            toggleOptions(row);
        });

        // Ouve a adição de uma nova pergunta
        $(document).on('djnesting:added', function(event, inline) {
            if (inline.prefix.includes('pergunta')) {
                 const newRow = inline.row;
                 const optionsBlock = newRow.find('.inline-group');
                 if (optionsBlock.length) {
                     // --- GARANTE QUE COMECE ESCONDIDO ---
                     optionsBlock.hide();
                 }
                 // Aplica estado inicial e placeholder
                 toggleOptions(newRow); // Verifica se já deve mostrar (caso o select já venha com valor)
                 addPlaceholder(newRow);
            }
        });

        // Roda as funções para as perguntas já existentes ao carregar
        setTimeout(function() {
            $('#perguntas-group .inline-related').each(function() {
                const $row = $(this);
                // --- GARANTE QUE OPÇÕES NÃO VISÍVEIS COMECEM ESCONDIDAS ---
                const selectVal = $row.find('.field-tipo_resposta select').val();
                const typesWithOptions = ['UNICA_ESCOLHA', 'MULTIPLA_ESCOLHA'];
                if (!typesWithOptions.includes(selectVal)) {
                     $row.find('.inline-group').hide();
                }
                // Roda o resto
                toggleOptions($row);
                addPlaceholder($row);
            });
        }, 250);
    });
})(jQuery); // Garante que $ é jQuery