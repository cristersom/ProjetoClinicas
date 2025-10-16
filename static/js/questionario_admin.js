(function($) {
    $(document).ready(function() {
        // Função para mostrar ou esconder o bloco de opções de resposta
        function toggleOptions(selectElement) {
            const perguntaBlock = $(selectElement).closest('.inline-related');
            const optionsBlock = perguntaBlock.find('.inline-group'); // O bloco 'Opções de Resposta'
            const selectedType = $(selectElement).val();
            const typesWithOptions = ['UNICA_ESCOLHA', 'MULTIPLA_ESCOLHA'];

            if (typesWithOptions.includes(selectedType)) {
                optionsBlock.slideDown(); // Mostra o bloco com uma animação suave
            } else {
                optionsBlock.slideUp(); // Esconde o bloco com uma animação suave
            }
        }

        // Delega o evento de 'change' para o container principal das perguntas.
        // Isso garante que a função funcione tanto para perguntas existentes quanto para novas.
        $('#perguntas-group').on('change', '.field-tipo_resposta select', function() {
            toggleOptions(this);
        });

        // Executa a função para todas as perguntas já existentes quando a página carrega,
        // mas com um pequeno atraso para garantir que todos os elementos do nested_admin foram renderizados.
        setTimeout(function() {
            $('.field-tipo_resposta select').each(function() {
                toggleOptions(this);
            });
        }, 100);
    });
})(django.jQuery);