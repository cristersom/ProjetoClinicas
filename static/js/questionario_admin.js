(function($) {

    // Função para esconder/mostrar opções
    function toggleOptions(row) {
        const $row = $(row);
        const selectElement = $row.find('.field-tipo_resposta select');
        // Seleciona o container das opções DENTRO da linha da pergunta
        const optionsContainer = $row.find('.inline-group');

        if (!selectElement.length || !optionsContainer.length) return;

        const selectedType = selectElement.val();
        const typesWithOptions = ['UNICA_ESCOLHA', 'MULTIPLA_ESCOLHA'];

        optionsContainer.toggle(typesWithOptions.includes(selectedType));
    }

    // Função para adicionar TODOS os placeholders
    function applyPlaceholders(element) {
        const $element = $(element);

        // Placeholder Pergunta
        const questionInput = $element.find('.field-texto_pergunta input[type="text"]');
        if (questionInput.length && !questionInput.attr('placeholder')) {
            questionInput.attr('placeholder', 'Pergunta');
        }

        // Placeholder Tipo Resposta (Select)
        const typeSelect = $element.find('.field-tipo_resposta select');
        if (typeSelect.length) {
            if (typeSelect.find('option[value=""][disabled]').length === 0) {
                 typeSelect.prepend('<option value="" disabled selected style="color: #80868b;">-- Tipo --</option>');
            }
            if (!typeSelect.val()) { typeSelect.val(""); } // Força placeholder se vazio
        }

        // Placeholder Opção (dentro do bloco de opções)
        // Percorre cada linha de opção DENTRO do elemento atual (se for uma pergunta)
         $element.find('.dynamic-opcaoresposta_set').each(function(){
             const optionInput = $(this).find('.field-texto input[type="text"]');
             if (optionInput.length && !optionInput.attr('placeholder')) {
                optionInput.attr('placeholder', 'Opção');
             }
         });
         // Ou, se o próprio elemento for uma linha de opção adicionada
         if ($element.hasClass('dynamic-opcaoresposta_set')) {
              const optionInput = $element.find('.field-texto input[type="text"]');
             if (optionInput.length && !optionInput.attr('placeholder')) {
                optionInput.attr('placeholder', 'Opção');
             }
         }
    }


    $(document).ready(function() {

        // Renomear botões (simplificado)
        function renameButtons() {
            // Botão Adicionar Opção
            $('.inline-group .djn-add-item a').text('Adicionar Opção');
            // Botão Adicionar Pergunta
            $('#perguntas-group > .djn-add-item a').text('Adicionar Pergunta');
        }
        // Roda a renomeação repetidamente
        setInterval(renameButtons, 700);


        // Ouve a mudança no dropdown Tipo Resposta
        $('body').on('change', '#perguntas-group .field-tipo_resposta select', function() {
            // Acha a linha da pergunta (pai .inline-related)
            const questionRow = $(this).closest('.inline-related');
            toggleOptions(questionRow);
        });

        // Ouve a adição de um novo inline (evento do nested_admin)
        $(document).on('djnesting:added', function(event, inline) {
            const newRow = inline.row; // A linha TR adicionada

            // Se for uma PERGUNTA (tem a classe .inline-related)
            if ($(newRow).hasClass('inline-related')) {
                 // Esconde o bloco de opções imediatamente
                 const optionsContainer = $(newRow).find('.inline-group');
                 if (optionsContainer.length) {
                     optionsContainer.hide();
                 }
                 // Aplica placeholders à nova pergunta e tipo
                 applyPlaceholders(newRow);
            }
             // Se for uma OPÇÃO (tem a classe dynamic-opcaoresposta_set)
            else if ($(newRow).hasClass('dynamic-opcaoresposta_set')) {
                 // Aplica placeholder à nova opção
                 applyPlaceholders(newRow);
            }
        });


        // Aplica lógica aos elementos existentes após um delay maior
        setTimeout(function() {
            $('#perguntas-group .inline-related').each(function() {
                const $questionRow = $(this);
                applyPlaceholders($questionRow); // Aplica placeholders
                toggleOptions($questionRow); // Esconde/mostra opções iniciais
            });
            renameButtons(); // Renomeia botões iniciais
        }, 1000); // Delay de 1 segundo

    });

})(jQuery);