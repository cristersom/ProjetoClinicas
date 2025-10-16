// Espera o DOM carregar, usando o namespace do Django para evitar conflitos
(function($) {
    $(document).ready(function() {
        // Função para mostrar ou esconder as opções de resposta
        function toggleOptions(selectElement) {
            // Encontra o 'bloco' da pergunta onde o select está
            const perguntaBlock = $(selectElement).closest('.inline-related');
            // Encontra a sub-seção de opções dentro do bloco da pergunta
            const optionsBlock = perguntaBlock.find('.inline-group');
            const selectedType = $(selectElement).val();

            // Tipos de pergunta que precisam de opções
            const typesWithOptions = ['UNICA_ESCOLHA', 'MULTIPLA_ESCOLHA'];

            if (typesWithOptions.includes(selectedType)) {
                optionsBlock.show(); // Mostra as opções
            } else {
                optionsBlock.hide(); // Esconde as opções
            }
        }

        // Executa a função para todas as perguntas que já existem na página quando ela carrega
        $('.field-tipo_resposta select').each(function() {
            toggleOptions(this);
        });

        // Adiciona um 'listener' que executa a função toda vez que um tipo de resposta é alterado
        // Usamos 'change' e especificamos o seletor para funcionar com perguntas novas que são adicionadas dinamicamente
        $('#perguntas-group').on('change', '.field-tipo_resposta select', function() {
            toggleOptions(this);
        });
    });
})(django.jQuery);