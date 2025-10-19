(function($) { // '$' é django.jQuery
    console.log("[QAdmin V12] Script loaded.");

    // Função toggleOptions (Seletores Genéricos dentro da linha)
    function toggleOptions(row) {
        const $row = $(row); // Assume que row é o TR da Pergunta
        const rowId = $row.attr('id') || $row.index();
        console.log(`[QAdmin V12] Attempting toggleOptions for row: ${rowId}`);

        // Tenta achar o select de tipo de forma mais genérica DENTRO da linha
        const selectElement = $row.find('select[name$="-tipo_resposta"]'); // Procura select cujo nome termina com '-tipo_resposta'

        // Tenta achar o container de opções (geralmente .inline-group) DENTRO da linha
        const optionsContainer = $row.find('.inline-group'); // Acha o primeiro .inline-group dentro da linha

        if (!selectElement.length) { console.warn(`[QAdmin V12] Toggle: Select not found in ${rowId}`); return; }
        if (!optionsContainer.length) { console.warn(`[QAdmin V12] Toggle: Options Container (.inline-group) not found in ${rowId}`); return; }

        const selectedType = selectElement.val();
        const typesWithOptions = ['UNICA_ESCOLHA', 'MULTIPLA_ESCOLHA'];
        const shouldShow = typesWithOptions.includes(selectedType);

        console.log(`[QAdmin V12] Toggle: Row=${rowId}, Type=${selectedType}, ShouldShow=${shouldShow}`);
        // Usar show/hide simples
        optionsContainer.toggle(shouldShow);
    }

    // --- Execução Principal ---
    $(document).ready(function() {
        console.log("[QAdmin V12] Document Ready");

        const perguntaPrefix = 'perguntas'; // Ajuste se o prefixo for diferente

        // Ouve a mudança no dropdown Tipo Resposta (com seletor genérico)
        // Usa 'body' para pegar elementos adicionados dinamicamente
        $('body').on('change', `tr[id^='${perguntaPrefix}-'] select[name$='-tipo_resposta']`, function() {
             console.log("[QAdmin V12] Select change detected");
             // Sobe para o TR da pergunta (que deve ter ID começando com o prefixo)
             const row = $(this).closest(`tr[id^='${perguntaPrefix}-']`);
             if (row.length) {
                toggleOptions(row);
             } else {
                 console.error("[QAdmin V12] Change event: Could not find parent question row (TR).");
             }
        });

        // Ouve evento 'formset:added' do Django
        $(document).on('formset:added', function(event, $row, formsetName) {
            console.log(`[QAdmin V12] formset:added triggered for formset '${formsetName}'. Row ID: ${$row.attr('id')}`);

            // Espera um ciclo de eventos para o DOM atualizar
            setTimeout(function() {
                 // Verifica se a linha adicionada é uma PERGUNTA
                 if ($row.is(`tr[id^='${perguntaPrefix}-']`) && !$row.hasClass('djn-empty-form')) {
                    console.log(`[QAdmin V12] Added row is a question: ${$row.attr('id')}. Applying initial toggle.`);
                    // Garante que as opções comecem escondidas
                    const optionsContainer = $row.find('.inline-group');
                    if(optionsContainer.length) {
                        optionsContainer.hide();
                         // Chama toggle para aplicar o estado correto baseado no select inicial
                         toggleOptions($row);
                    } else {
                         console.warn(`[QAdmin V12] Added question ${$row.attr('id')} has no options container.`);
                    }
                    // Adicionar placeholders aqui DEPOIS se o toggle funcionar
                    // addQuestionPlaceholders($row);
                }
                // (Lógica para placeholder de opção viria aqui depois)
                // else if ($row.is("tr[id*='opcaoresposta']")) { ... }

                // (Lógica para renomear botão viria aqui depois)
                // renameButtons();

            }, 50); // Delay mínimo
        });

        // Aplica toggle inicial aos elementos já presentes (com delay)
        // Necessário porque nested_admin pode carregar depois do ready
        function runInitialLogic() {
            console.log("[QAdmin V12] Applying initial toggle logic...");
            let count = 0;
             $(`tr[id^='${perguntaPrefix}-']`).not('.djn-empty-form').each(function() {
                 toggleOptions(this); // Aplica toggle inicial
                 count++;
            });
             console.log(`[QAdmin V12] Initial toggle logic applied to ${count} questions.`);
             // (Renomear botões e placeholders viria aqui depois)
        }
        setTimeout(runInitialLogic, 1000); // Delay de 1 segundo

    }); // Fim Document Ready

})(django.jQuery); // Passa django.jQuery como '$'