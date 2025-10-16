(function($) {
    $(document).ready(function() {
        // Função para mostrar ou esconder o bloco de opções
        function toggleOptions(row) {
            const selectElement = row.find('.field-tipo_resposta select');
            const optionsBlock = row.find('.inline-group'); // O bloco 'Opções de Resposta'
            const selectedType = selectElement.val();
            const typesWithOptions = ['UNICA_ESCOLHA', 'MULTIPLA_ESCOLHA'];

            if (typesWithOptions.includes(selectedType)) {
                optionsBlock.slideDown(); // Mostra o bloco com uma animação
            } else {
                optionsBlock.slideUp(); // Esconde o bloco com uma animação
            }
        }

        // Delega o evento 'change' para o container principal das perguntas.
        // Isso garante que a função funcione para perguntas existentes e novas.
        $('#perguntas-group').on('change', '.field-tipo_resposta select', function() {
            const row = $(this).closest('.inline-related');
            toggleOptions(row);
        });

        // Delega o evento 'added' do nested-admin para o documento.
        $(document).on('djnesting:added', function(event, inline) {
            // Verifica se a nova linha é uma pergunta
            if (inline.prefix.includes('pergunta')) {
                // Esconde o bloco de opções da nova pergunta por padrão
                inline.row.find('.inline-group').hide();
            }
        });

        // Executa a função para todas as perguntas já existentes quando a página carrega
        setTimeout(function() {
            $('#perguntas-group .inline-related').each(function() {
                toggleOptions($(this));
            });
        }, 150); // Um pequeno atraso para o nested-admin renderizar tudo
    });
})(django.jQuery);