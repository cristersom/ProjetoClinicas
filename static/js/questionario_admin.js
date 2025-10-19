(function($) { // '$' é django.jQuery
    console.log("[QAdmin V13] Script loaded.");

    // Função toggleOptions (Simplificada ao máximo)
    function toggleOptions(questionRow) {
        const $row = $(questionRow); // TR da pergunta
        const rowId = $row.attr('id') || $row.index();
        console.log(`[QAdmin V13] toggleOptions called for row: ${rowId}`);

        // Tenta achar o select DENTRO da linha
        const selectElement = $row.find('select[name$="-tipo_resposta"]');
        // Tenta achar o container de opções DENTRO da linha
        const optionsContainer = $row.find('.inline-group'); // O container mais provável

        if (!selectElement.length) {
            console.warn(`[QAdmin V13] Toggle: Select not found in ${rowId}`); return;
        }
        if (!optionsContainer.length) {
            // Se não achar .inline-group, tenta achar o fieldset diretamente
            const fallbackContainer = $row.find('fieldset.module');
             if(!fallbackContainer.length){
                console.warn(`[QAdmin V13] Toggle: Options Container (.inline-group or fieldset.module) not found in ${rowId}`); return;
             }
             // Usa o fallback se encontrado
             optionsContainer = fallbackContainer;
        }


        const selectedType = selectElement.val();
        const typesWithOptions = ['UNICA_ESCOLHA', 'MULTIPLA_ESCOLHA'];
        const shouldShow = typesWithOptions.includes(selectedType);

        console.log(`[QAdmin V13] Toggle: Row=${rowId}, Type=${selectedType}, ShouldShow=${shouldShow}`);
        // Força show/hide
        if (shouldShow) {
             optionsContainer.show();
        } else {
             optionsContainer.hide();
        }
    }

    // --- Execução Principal ---
    $(document).ready(function() {
        console.log("[QAdmin V13] Document Ready");

        const perguntaPrefix = 'perguntas'; // Prefixo do formset de perguntas

        // Aplica toggle inicial aos elementos já presentes
        function runInitialToggle() {
            console.log("[QAdmin V13] Applying initial toggle logic...");
            let count = 0;
             // Seleciona todas as linhas de pergunta que NÃO são o template vazio
             $(`#${perguntaPrefix}-group tbody tr.dynamic-${perguntaPrefix}_set`).not('.djn-empty-form').each(function() {
                 toggleOptions(this); // Aplica toggle inicial
                 count++;
            });
             console.log(`[QAdmin V13] Initial toggle logic applied to ${count} questions.`);
             // Se não achou, tenta de novo (nested_admin pode ser lento)
             if (count === 0 && !$(document).data('initial-toggle-failed')) {
                 $(document).data('initial-toggle-failed', true);
                 console.warn("[QAdmin V13] No initial questions found, retrying toggle...");
                 setTimeout(runInitialToggle, 1500);
             }
        }
        setTimeout(runInitialToggle, 500); // Delay inicial


        // Ouve a mudança no dropdown Tipo Resposta
        $('body').on('change', `select[name$="-tipo_resposta"]`, function() {
             console.log("[QAdmin V13] Select change detected");
             // Sobe para o TR da pergunta (o TR pai mais próximo com um ID)
             const row = $(this).closest(`tr[id^='${perguntaPrefix}-']`);
             if (row.length) {
                toggleOptions(row);
             } else {
                 console.error("[QAdmin V13] Change event: Could not find parent question row (TR).");
             }
        });

        // Ouve evento 'formset:added'
        $(document).on('formset:added', function(event, $row, formsetName) {
             // $row aqui é a linha (TR) adicionada
             console.log(`[QAdmin V13] formset:added triggered for formset '${formsetName}'. Row ID: ${$row.attr('id')}`);

             // Verifica se a linha adicionada é uma PERGUNTA e não o template vazio
             if ($row.is(`tr[id^='${perguntaPrefix}-']`) && !$row.hasClass('djn-empty-form')) {
                 console.log(`[QAdmin V13] Added row is a question: ${$row.attr('id')}. Applying initial toggle.`);
                 // Garante que as opções comecem escondidas, DEPOIS aplica o toggle correto
                 const optionsContainer = $row.find('.inline-group'); // Tenta o container principal
                 if(optionsContainer.length) {
                     optionsContainer.hide(); // Esconde primeiro
                     // Chama toggle DEPOIS para garantir estado correto
                     setTimeout(function() { // Pequeno delay para garantir DOM
                        toggleOptions($row);
                     }, 10);
                 } else {
                      // Tenta o fallback se .inline-group não for encontrado logo
                      const fallbackContainer = $row.find('fieldset.module');
                      if(fallbackContainer.length){
                          fallbackContainer.hide();
                           setTimeout(function() { toggleOptions($row); }, 10);
                      } else {
                          console.warn(`[QAdmin V13] Added question ${$row.attr('id')} has no options container.`);
                      }
                 }
            }
            // (Ignoramos placeholders e botões por enquanto)
        });

    }); // Fim Document Ready

})(django.jQuery); // Passa django.jQuery como '$'