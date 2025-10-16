(function($) {
    // Função para mostrar ou esconder o bloco de opções de uma linha de pergunta
    function toggleOptions(row) {
        const selectElement = row.find('.field-tipo_resposta select');
        const optionsBlock = row.find('.inline-group'); // O bloco que contém as 'Opções de Resposta'
        const selectedType = selectElement.val();
        const typesWithOptions = ['UNICA_ESCOLHA', 'MULTIPLA_ESCOLHA'];

        if (typesWithOptions.includes(selectedType)) {
            optionsBlock.slideDown(); // Mostra o bloco com uma animação suave
        } else {
            optionsBlock.slideUp(); // Esconde o bloco com uma animação suave
        }
    }

    $(document).ready(function() {
        // 1. Usa delegação de eventos. Isso garante que a função funcione для
        //    perguntas que já existem e para novas perguntas que você adiciona dinamicamente.
        $('#perguntas-group').on('change', '.field-tipo_resposta select', function() {
            const row = $(this).closest('.inline-related');
            toggleOptions(row);
        });

        // 2. Garante que, quando uma NOVA pergunta é adicionada, suas opções comecem escondidas.
        $(document).on('djnesting:added', function(event, inline) {
            if (inline.prefix.includes('pergunta')) {
                inline.row.find('.inline-group').hide();
            }
        });

        // 3. Roda a função para todas as perguntas já existentes quando a página carrega.
        //    O pequeno atraso garante que a biblioteca nested-admin já tenha renderizado tudo.
        setTimeout(function() {
            $('#perguntas-group .inline-related').each(function() {
                toggleOptions($(this));
            });
        }, 150);
    });
})(django.jQuery);