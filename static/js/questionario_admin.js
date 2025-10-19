(function($) { // '$' é django.jQuery
    console.log("[QAdmin V14] Script loaded.");

    // Função toggleOptions (Verifica elementos)
    function toggleOptions(row) {
        const $row = $(row); // TR da pergunta
        if (!$row || $row.length === 0) return; // Verifica se a linha é válida
        const rowId = $row.attr('id') || $row.index();

        const selectElement = $row.find('td.field-tipo_resposta select');
        const optionsContainer = $row.find('td.original .inline-group > fieldset.module, td.original .inline-group > .djn-group');

        if (!selectElement.length) { console.warn(`[QAdmin V14] Toggle: Select not found in ${rowId}`); return; }
        if (!optionsContainer.length) { console.warn(`[QAdmin V14] Toggle: Options Container not found in ${rowId}`); return; }

        const selectedType = selectElement.val();
        const typesWithOptions = ['UNICA_ESCOLHA', 'MULTIPLA_ESCOLHA'];
        const shouldShow = typesWithOptions.includes(selectedType);

        // console.log(`[QAdmin V14] Toggle: Row=${rowId}, Type=${selectedType}, ShouldShow=${shouldShow}`);
        optionsContainer.toggle(shouldShow);
    }

    // Função addQuestionPlaceholders (Verifica elementos)
    function addQuestionPlaceholders(row) {
        const $row = $(row);
        if (!$row || $row.length === 0) return;
        const rowId = $row.attr('id') || $row.index();

        const questionInput = $row.find('td.field-texto_pergunta input[type="text"]');
        if (questionInput.length && !questionInput.attr('placeholder')) {
            questionInput.attr('placeholder', 'Digite sua pergunta aqui');
        }
         const typeSelect = $row.find('td.field-tipo_resposta select');
         if (typeSelect.length) {
            if (typeSelect.find('option[value=""][disabled]').length === 0) {
                 typeSelect.prepend('<option value="" disabled style="color: #80868b;">-- Tipo --</option>');
            }
            if (!typeSelect.val() || typeSelect.val() === "") { typeSelect.val(""); }
         }
    }

    // Função addOptionPlaceholder (Verifica elementos)
    function addOptionPlaceholder(optionRow) {
        const $optionRow = $(optionRow);
         if (!$optionRow || $optionRow.length === 0) return;
        const rowId = $optionRow.attr('id') || $optionRow.index();

        const optionInput = $optionRow.find('td.field-texto input[type="text"]');
        if (optionInput.length && !optionInput.attr('placeholder')) {
            optionInput.attr('placeholder', 'Opção');
        }
    }

    // Aplica lógica (Placeholders + Toggle Inicial)
    function applyLogicToQuestionRow(row) {
        const $row = $(row);
        const logicFlag = 'logic-applied-v14';
        if (!$row || $row.length === 0 || $row.data(logicFlag) || $row.hasClass('djn-empty-form')) return;

        console.log("[QAdmin V14] Applying logic to Pergunta:", $row.attr('id') || $row.index());
        addQuestionPlaceholders($row);
        // Aplica placeholder a opções internas
        $row.find('tr.dynamic-opcaoresposta_set').each(function() {
            applyLogicToOptionRow(this);
        });
        toggleOptions($row); // Aplica toggle inicial
        $row.data(logicFlag, true);
    }

    function applyLogicToOptionRow(row) {
         const $row = $(row);
         const logicFlag = 'logic-applied-v14';
         if (!$row || $row.length === 0 || $row.data(logicFlag) || $row.hasClass('djn-empty-form')) return;

         console.log("[QAdmin V14] Applying logic to Opção:", $row.attr('id') || $row.index());
         addOptionPlaceholder($row);
         $row.data(logicFlag, true);
    }

    // Renomeia botões
    function renameButtons() {
        // Botão Adicionar Pergunta
        const $addQuestionBtn = $('#perguntas-group > fieldset.module > div.djn-add-item a');
        if ($addQuestionBtn.length && !$addQuestionBtn.text().includes('Adicionar Pergunta')) {
            $addQuestionBtn.text('Adicionar Pergunta');
        }
        // Botão Adicionar Opção
        $('.inline-group fieldset.module > div.djn-add-item a, .inline-group div.djn-group > div.djn-add-item a').each(function(){
            const $btn = $(this);
            if (!$btn.closest('.djn-empty-form').length && !$btn.text().includes('Adicionar Opção')) {
                $btn.text('Adicionar Opção');
            }
        });
    }

    // --- Execução Principal ---
    $(document).ready(function() {
        console.log("[QAdmin V14] Document Ready");

        const perguntaPrefix = 'perguntas'; // Prefixo do formset de perguntas

        // Aplica lógica inicial aos elementos já presentes (com delay robusto)
        function runInitialLogic() {
            console.log("[QAdmin V14] Running initial logic...");
            let count = 0;
             $(`tr[id^='${perguntaPrefix}-']`).not('.djn-empty-form').each(function() {
                 applyLogicToQuestionRow(this);
                 count++;
            });
             renameButtons(); // Renomeia botões iniciais
             console.log(`[QAdmin V14] Initial logic applied to ${count} questions.`);
        }
        // Tenta rodar depois de um tempo maior, assumindo que nested_admin terminou
        setTimeout(runInitialLogic, 1500); // 1.5 segundos


        // Ouve a mudança no dropdown Tipo Resposta (Seletor Corrigido)
        $('body').on('change', `select[name$="-tipo_resposta"]`, function() {
             console.log("[QAdmin V14] Select change detected");
             // Sobe para o TR da pergunta (o TR pai mais próximo com ID que começa com 'perguntas-')
             const row = $(this).closest(`tr[id^='${perguntaPrefix}-']`); // Confia no ID gerado
             if (row.length) {
                console.log("[QAdmin V14] Found parent row:", row.attr('id'));
                toggleOptions(row);
             } else {
                 console.error("[QAdmin V14] Change event: Could not find parent question row (TR).");
             }
        });

        // Ouve evento 'formset:added'
        $(document).on('formset:added', function(event, $row, formsetName) {
             // VERIFICA se $row é um objeto jQuery válido ANTES de usar
             if ($row && $row.length > 0) {
                const rowId = $row.attr('id') || 'NO ID';
                console.log(`[QAdmin V14] formset:added triggered for formset '${formsetName}'. Row ID: ${rowId}`);

                // Espera um ciclo de eventos
                setTimeout(function() {
                     // Verifica se a linha adicionada é uma PERGUNTA
                     if ($row.is(`tr[id^='${perguntaPrefix}-']`) && !$row.hasClass('djn-empty-form')) {
                        console.log(`[QAdmin V14] Added row is a question: ${rowId}. Applying logic.`);
                        applyLogicToQuestionRow($row); // Aplica placeholders e toggle inicial
                        // Força esconder opções recém-adicionadas
                         const optionsContainer = $row.find('.inline-group > fieldset.module, .inline-group > .djn-group');
                         if(optionsContainer.length) {
                             optionsContainer.hide();
                             // Re-aplica toggle para garantir estado correto
                             toggleOptions($row);
                         }
                    }
                    // Se for uma OPÇÃO
                    else if ($row.is("tr[id*='opcaoresposta']") && !$row.hasClass('djn-empty-form')) {
                        applyLogicToOptionRow($row);
                    }
                    renameButtons(); // Renomeia botões
                }, 50);
             } else {
                 console.error("[QAdmin V14] formset:added event received invalid $row:", $row);
             }
        });

    }); // Fim Document Ready

})(django.jQuery); // Passa django.jQuery como '$'