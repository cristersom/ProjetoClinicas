// Usa o wrapper do Django Admin para garantir que django.jQuery esteja pronto
(function($) { // '$' aqui dentro agora é o 'django.jQuery'
    console.log("questionario_admin.js loaded using django.jQuery");

    // Função toggleOptions (com logs)
    function toggleOptions(row) {
        const $row = $(row);
        const selectElement = $row.find('.field-tipo_resposta select');
        const optionsContainer = $row.find('.inline-group'); // Container padrão das opções

        if (!selectElement.length) {
            console.warn("Toggle: Select não encontrado em", $row.attr('id')); return;
        }
        if (!optionsContainer.length) {
             console.warn("Toggle: OptionsContainer não encontrado em", $row.attr('id')); return;
        }

        const selectedType = selectElement.val();
        const typesWithOptions = ['UNICA_ESCOLHA', 'MULTIPLA_ESCOLHA'];
        const shouldShow = typesWithOptions.includes(selectedType);

        console.log(`Toggle: Row=${$row.attr('id')}, Type=${selectedType}, ShouldShow=${shouldShow}`);
        // Usar show/hide simples para teste
        if (shouldShow) {
            optionsContainer.show();
        } else {
            optionsContainer.hide();
        }
    }

    // Função addQuestionPlaceholders (com logs)
    function addQuestionPlaceholders(row) {
        const $row = $(row);
        const questionInput = $row.find('.field-texto_pergunta input[type="text"]');
        if (questionInput.length && !questionInput.attr('placeholder')) {
            questionInput.attr('placeholder', 'Digite sua pergunta aqui');
            console.log(`Placeholder Pergunta adicionado a ${$row.attr('id')}`);
        }
         const typeSelect = $row.find('.field-tipo_resposta select');
         if (typeSelect.length) {
            if (typeSelect.find('option[value=""][disabled]').length === 0) {
                 typeSelect.prepend('<option value="" disabled style="color: #80868b;">-- Selecione o Tipo --</option>');
                 console.log(`Placeholder Tipo adicionado a ${$row.attr('id')}`);
            }
            if (!typeSelect.val() || typeSelect.val() === "") {
                typeSelect.val(""); // Força seleção
            }
         }
    }

    // Função addOptionPlaceholder (com logs)
    function addOptionPlaceholder(optionRow) {
        const $optionRow = $(optionRow);
        // Tenta pegar pelo ID que termina em '-texto' E é text input
        const optionInput = $optionRow.find('input[type="text"][id$="-texto"]');
        if (optionInput.length && !optionInput.attr('placeholder')) {
            optionInput.attr('placeholder', 'Opção de resposta');
             console.log(`Placeholder Opção adicionado a ${$optionRow.attr('id')}`);
        } else if (!optionInput.length) {
             console.warn(`Placeholder Opção: Input não encontrado em ${$optionRow.attr('id')}`);
        }
    }

    // Aplica lógica a um elemento
    function applyLogicToElement(element) {
         const $element = $(element);
         const logicFlag = 'logic-applied-v6'; // Nova flag

         if ($element.data(logicFlag)) return;

         if ($element.hasClass('inline-related')) { // É uma Pergunta
             console.log("Aplicando lógica a Pergunta:", $element.attr('id'));
             addQuestionPlaceholders($element);
             // Aplica a opções internas
             $element.find('.dynamic-opcaoresposta_set').each(function() { applyLogicToElement(this); });
             // Aplica toggle DEPOIS de processar filhos
             toggleOptions($element);
             $element.data(logicFlag, true);
         }
         else if ($element.hasClass('dynamic-opcaoresposta_set')) { // É uma Opção
             console.log("Aplicando lógica a Opção:", $element.attr('id'));
             addOptionPlaceholder($element);
             $element.data(logicFlag, true);
         }
    }

    // Renomeia botões (com logs)
    function renameButtons() {
        const $addQuestionBtn = $('#perguntas-group > .djn-add-item a');
        if ($addQuestionBtn.length && $addQuestionBtn.text() !== 'Adicionar Pergunta') {
            $addQuestionBtn.text('Adicionar Pergunta');
            console.log("Botão 'Adicionar Pergunta' renomeado.");
        }
        $('.inline-group .djn-add-item a').each(function(){
            const $addOptionBtn = $(this);
            if ($addOptionBtn.text() !== 'Adicionar Opção') {
                $addOptionBtn.text('Adicionar Opção');
                console.log("Botão 'Adicionar Opção' renomeado em:", $addOptionBtn.closest('.inline-related').attr('id'));
            }
        });
    }

    // --- Execução Principal ---
    $(document).ready(function() {
        console.log("Document Ready");

        // Ouve a mudança no dropdown
        $('body').on('change', '#perguntas-group .field-tipo_resposta select', function() {
            console.log("Select change detectado");
            const row = $(this).closest('.inline-related');
            toggleOptions(row);
        });

        // Ouve adição de inline
        $(document).on('djnesting:added', function(event, inline) {
            const newRow = inline.row;
            console.log("Inline adicionado:", $(newRow).attr('id'));
            applyLogicToElement(newRow); // Aplica placeholders
            // Esconde opções da nova pergunta imediatamente
            if ($(newRow).hasClass('inline-related')) {
                 const optionsContainer = $(newRow).find('> .inline-group');
                 if(optionsContainer.length) optionsContainer.hide();
                 // Chama toggle para garantir estado inicial correto
                 toggleOptions(newRow);
            }
            // Renomeia botões de novo
            renameButtons();
        });

        // Aplica lógica inicial com delay
        setTimeout(function() {
            console.log("Aplicando lógica inicial (Timeout)...");
            $('#perguntas-group .inline-related, #perguntas-group .dynamic-opcaoresposta_set').each(function() {
                applyLogicToElement(this);
            });
            renameButtons(); // Renomeia botões iniciais
            console.log("Lógica inicial (Timeout) concluída.");
        }, 1000); // 1 segundo de delay
    });

})(django.jQuery); // Passa django.jQuery como '$'