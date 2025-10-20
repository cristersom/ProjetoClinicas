(function($) { // '$' é django.jQuery
    console.log("[QAdmin V18 - Wide Search] Script loaded.");

    // Função toggleOptions (Busca Ampla)
    function toggleOptions(selectElement) {
        const $select = $(selectElement);
        // Tenta achar a linha/container da PERGUNTA de várias formas
        const $questionContainer = $select.closest('.inline-related'); // Método 1: Pelo .inline-related (se existir)
        const $questionRow = $select.closest('tr'); // Método 2: Pelo TR pai mais próximo

        if (!$questionContainer.length && !$questionRow.length) {
            console.error("[QAdmin V18] Toggle: Could not find parent container (.inline-related or TR) for select:", $select.attr('name'));
            return;
        }

        // Usa o container que foi encontrado (prioriza .inline-related se existir)
        const $searchContext = $questionContainer.length ? $questionContainer : $questionRow;
        const contextId = $searchContext.attr('id') || $searchContext.index();
        console.log(`[QAdmin V18] toggleOptions called for context: ${contextId}`);

        // Tenta achar o container de opções DENTRO do contexto encontrado
        // Busca por .inline-group em qualquer nível DENTRO do contexto
        let optionsContainer = $searchContext.find('.inline-group');

        if (!optionsContainer.length) {
             // Fallback: Tenta achar um fieldset que NÃO seja o fieldset dos campos principais
             optionsContainer = $searchContext.find('fieldset.module').not(':has(select[name$="-tipo_resposta"])');
             if(!optionsContainer.length){
                 console.warn(`[QAdmin V18] Toggle: Options Container (.inline-group or fieldset.module) not found within ${contextId}. Cannot toggle.`);
                 return; // Sai se não achar
             }
             console.log(`[QAdmin V18] Toggle: Using fallback options container (fieldset) in ${contextId}`);
        } else {
             console.log(`[QAdmin V18] Toggle: Found options container (.inline-group) in ${contextId}`);
        }


        const selectedType = $select.val();
        const typesWithOptions = ['UNICA_ESCOLHA', 'MULTIPLA_ESCOLHA'];
        const shouldShow = typesWithOptions.includes(selectedType);

        console.log(`[QAdmin V18] Toggle: Context=${contextId}, Type=${selectedType}, ShouldShow=${shouldShow}`);
        // Força show/hide
        optionsContainer.toggle(shouldShow);
    }

    // --- Execução Principal ---
    $(document).ready(function() {
        console.log("[QAdmin V18] Document Ready");

        // Aplica toggle inicial (com busca ampla)
        function runInitialToggle() {
            console.log("[QAdmin V18] Applying initial toggle logic...");
            let count = 0;
             // Seleciona TODOS os selects de tipo_resposta visíveis
             $('select[name$="-tipo_resposta"]').not('.djn-empty-form select').each(function() {
                 try {
                     // Tenta aplicar toggle diretamente ao select encontrado
                     toggleOptions(this);
                     count++;
                 } catch (e) {
                     console.error("[QAdmin V18] Error during initial toggle:", e, "on select:", $(this).attr('name'));
                 }
            });
             console.log(`[QAdmin V18] Initial toggle logic attempted on ${count} selects.`);
        }
        // Roda APÓS um delay maior
        setTimeout(runInitialToggle, 2000); // 2 segundos


        // Ouve a mudança em QUALQUER select de tipo_resposta
        $(document).on('change', 'select[name$="-tipo_resposta"]', function() {
             console.log("[QAdmin V18] Select change detected");
             try {
                 toggleOptions(this); // 'this' é o elemento select que mudou
             } catch (e) {
                  console.error("[QAdmin V18] Error during change toggle:", e, "on select:", $(this).attr('name'));
             }
        });

        // REMOVIDO: Listener para formset:added
        // REMOVIDO: Lógica de placeholders
        // REMOVIDO: Lógica de renomear botões

    }); // Fim Document Ready

})(django.jQuery); // Passa django.jQuery como '$'