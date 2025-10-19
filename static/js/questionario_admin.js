(function($) { // '$' é django.jQuery
    console.log("[QAdmin V10] Script loaded.");

    // Função toggleOptions (Seletores ajustados para layout padrão)
    function toggleOptions(row) {
        const $row = $(row);
        const rowId = $row.attr('id') || $row.index();
        const selectElement = $row.find('td.field-tipo_resposta select'); // Campo tipo está numa TD
        // Container das opções é um fieldset DENTRO do .inline-group (que está dentro de uma TD no TR da pergunta)
        const optionsContainer = $row.find('td.original > .inline-group > fieldset.module, td.original > .inline-group > .djn-group'); // Acha dentro da célula 'original'

        if (!selectElement.length) { /* console.warn(`[QAdmin V10] Toggle: Select not found in ${rowId}`); */ return; }
        if (!optionsContainer.length) { /* console.warn(`[QAdmin V10] Toggle: Options Container not found in ${rowId}`); */ return; }

        const selectedType = selectElement.val();
        const typesWithOptions = ['UNICA_ESCOLHA', 'MULTIPLA_ESCOLHA'];
        const shouldShow = typesWithOptions.includes(selectedType);

        // console.log(`[QAdmin V10] Toggle: Row=${rowId}, Type=${selectedType}, ShouldShow=${shouldShow}`);
        optionsContainer.toggle(shouldShow);
    }

    // Função addQuestionPlaceholders (Seletores ajustados)
    function addQuestionPlaceholders(row) {
        const $row = $(row);
        const rowId = $row.attr('id') || $row.index();
        // Input da pergunta está em td.field-texto_pergunta
        const questionInput = $row.find('td.field-texto_pergunta input[type="text"]');
        if (questionInput.length && !questionInput.attr('placeholder')) {
            questionInput.attr('placeholder', 'Digite sua pergunta aqui');
            // console.log(`[QAdmin V10] Placeholder Pergunta added to ${rowId}`);
        }
         // Select do tipo está em td.field-tipo_resposta
         const typeSelect = $row.find('td.field-tipo_resposta select');
         if (typeSelect.length) {
            if (typeSelect.find('option[value=""][disabled]').length === 0) {
                 typeSelect.prepend('<option value="" disabled style="color: #80868b;">-- Selecione o Tipo --</option>');
                 // console.log(`[QAdmin V10] Placeholder Tipo added to ${rowId}`);
            }
            if (!typeSelect.val() || typeSelect.val() === "") { typeSelect.val(""); }
         }
    }

    // Função addOptionPlaceholder (Seletores ajustados)
    function addOptionPlaceholder(optionRow) {
        const $optionRow = $(optionRow);
        const rowId = $optionRow.attr('id') || $optionRow.index();
        // Input da opção está em td.field-texto
        const optionInput = $optionRow.find('td.field-texto input[type="text"]');
        if (optionInput.length && !optionInput.attr('placeholder')) {
            optionInput.attr('placeholder', 'Opção de resposta');
            // console.log(`[QAdmin V10] Placeholder Opção added to ${rowId}`);
        }
    }

    // Aplica lógica a um elemento (Pergunta ou Opção)
    function applyLogicToElement(element) {
         const $element = $(element);
         const logicFlag = 'logic-applied-v10';

         if ($element.data(logicFlag) || $element.hasClass('djn-empty-form')) return; // Não processa template vazio

         // Verifica se é uma linha de PERGUNTA (TR dentro do tbody de #perguntas-group)
         if ($element.is('#perguntas-group tbody tr.dynamic-perguntas_set')) { // Ajuste prefixo se necessário
             // console.log("[QAdmin V10] Applying logic to Pergunta:", $element.attr('id') || $element.index());
             addQuestionPlaceholders($element);
             // Aplica a opções internas JÁ EXISTENTES
             $element.find('tr.dynamic-opcaoresposta_set').each(function() { applyLogicToElement(this); }); // Acha opções DENTRO desta pergunta
             // Aplica toggle DEPOIS
             toggleOptions($element);
             $element.data(logicFlag, true);
         }
         // Verifica se é uma linha de OPÇÃO (TR dentro do tbody de um .inline-group)
         else if ($element.is('.inline-group tbody tr.dynamic-opcaoresposta_set')) { // Ajuste prefixo se necessário
             // console.log("[QAdmin V10] Applying logic to Opção:", $element.attr('id') || $element.index());
             addOptionPlaceholder($element);
             $element.data(logicFlag, true);
         }
    }

    // Renomeia botões (Seletores Corrigidos para layout padrão)
    function renameButtons() {
        // console.log("[QAdmin V10] Attempting to rename buttons...");
        // Botão Adicionar Pergunta (Link dentro de div.djn-add-item que é filho do fieldset principal)
        const $addQuestionBtn = $('#perguntas-group > fieldset.module > div.djn-add-item a');
        if ($addQuestionBtn.length && $addQuestionBtn.text().includes('Pergunta')) { // Verifica se já não está certo
             if ($addQuestionBtn.text() !== 'Adicionar Pergunta') {
                 $addQuestionBtn.text('Adicionar Pergunta');
                 // console.log("[QAdmin V10] Botão 'Adicionar Pergunta' RENAMED.");
             }
        } else {
             // console.warn("[QAdmin V10] Botão 'Adicionar Pergunta' not found or text incorrect.");
        }

        // Botão Adicionar Opção (Link dentro de div.djn-add-item que é filho do fieldset interno das opções)
        $('.inline-group fieldset.module > div.djn-add-item a').each(function(){
            const $addOptionBtn = $(this);
            // Evita renomear o botão do template vazio
            if ($addOptionBtn.closest('.djn-empty-form').length === 0 && $addOptionBtn.text() !== 'Adicionar Opção') {
                $addOptionBtn.text('Adicionar Opção');
                // console.log("[QAdmin V10] Botão 'Adicionar Opção' RENAMED.");
            }
        });
    }

    // --- Execução Principal ---
    $(document).ready(function() {
        console.log("[QAdmin V10] Document Ready");

        // Ouve a mudança no dropdown Tipo Resposta
        // Target mais específico no select dentro da célula
        $('body').on('change', '#perguntas-group td.field-tipo_resposta select', function() {
            // console.log("[QAdmin V10] Select change detected");
            // Sobe para o TR da pergunta
            const row = $(this).closest('tr.dynamic-perguntas_set'); // Ajuste prefixo se necessário
            toggleOptions(row);
        });

        // --- OBSERVAR MUDANÇAS NO DOM ---
        const observerTargetNode = document.getElementById('perguntas-group');
        if (observerTargetNode) {
            console.log("[QAdmin V10] Setting up MutationObserver.");
            const observer = new MutationObserver(function(mutations) {
                let addedElements = [];
                mutations.forEach(function(mutation) {
                    mutation.addedNodes.forEach(function(node) {
                        // Considera apenas elementos TR que são inlines
                        if (node.nodeType === 1 && node.tagName === 'TR' && ($(node).hasClass('dynamic-perguntas_set') || $(node).hasClass('dynamic-opcaoresposta_set'))) {
                            addedElements.push(node);
                        }
                    });
                });

                if (addedElements.length > 0) {
                    console.log("[QAdmin V10] Observer detected added nodes:", addedElements.length);
                    // Aplica lógica aos nós adicionados
                    $(addedElements).each(function(){
                        applyLogicToElement(this);
                        // Se for pergunta nova, garante opções escondidas e aplica toggle
                        if ($(this).hasClass('dynamic-perguntas_set')) {
                             const optionsContainer = $(this).find('.inline-group > fieldset.module, .inline-group > .djn-group');
                             if(optionsContainer.length) optionsContainer.hide();
                             toggleOptions(this); // Aplica estado correto
                        }
                    });
                    // Renomeia botões DEPOIS que os elementos foram adicionados
                    renameButtons();
                }
            });
            const config = { childList: true, subtree: true };
            observer.observe(observerTargetNode, config);
        } else {
             console.error("[QAdmin V10] Elemento #perguntas-group não encontrado para o MutationObserver.");
        }

        // Aplica lógica inicial aos elementos já presentes (com delay e verificação)
        function runInitialLogic() {
             console.log("[QAdmin V10] Running initial logic...");
             let foundElements = 0;
             $('#perguntas-group tbody tr.dynamic-perguntas_set, #perguntas-group tbody tr.dynamic-opcaoresposta_set').each(function() {
                 // Evita o template vazio
                 if (!$(this).hasClass('djn-empty-form')) {
                    applyLogicToElement(this);
                    foundElements++;
                 }
             });
             renameButtons(); // Renomeia botões iniciais
             console.log(`[QAdmin V10] Initial logic applied to ${foundElements} elements.`);
             // Se nenhum elemento foi encontrado, tenta de novo um pouco mais tarde
             if (foundElements === 0) {
                 setTimeout(runInitialLogic, 1500); // Tenta de novo após 1.5s
             }
        }
        setTimeout(runInitialLogic, 800); // Delay inicial de 0.8s

    }); // Fim Document Ready

})(django.jQuery); // Passa django.jQuery como '$'