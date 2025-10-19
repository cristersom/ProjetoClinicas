(function($) { // '$' é django.jQuery
    console.log("[QAdmin V16] Script loaded.");

    // Função toggleOptions (Busca a partir do select)
    function toggleOptions(selectElement) {
        const $select = $(selectElement);
        // Tenta subir APENAS UM NÍVEL para o TD e depois para o TR
        const $questionRow = $select.closest('tr'); // Busca o TR pai mais próximo

        if (!$questionRow.length) {
            console.error("[QAdmin V16] Toggle: Could not find parent TR for select:", $select.attr('name'));
            return; // Sai se não achar a linha
        }

        const rowId = $questionRow.attr('id') || $questionRow.index();
        console.log(`[QAdmin V16] toggleOptions called for row: ${rowId}`);

        // Tenta achar o container de opções DENTRO da linha da pergunta
        // Procura por .inline-group dentro de QUALQUER célula (td) da linha
        const optionsContainer = $questionRow.find('td .inline-group');

        if (!optionsContainer.length) {
            console.warn(`[QAdmin V16] Toggle: Options Container (.inline-group) not found in ${rowId}`);
            // Tenta um seletor de fallback mais específico se o primeiro falhar
            const fallbackContainer = $questionRow.find('td.original > .inline-group > fieldset.module, td.original > .inline-group > .djn-group');
            if (!fallbackContainer.length) {
                 console.error(`[QAdmin V16] Toggle: Fallback Options Container also not found in ${rowId}`);
                 return; // Sai se nenhum container for encontrado
            }
             optionsContainer = fallbackContainer; // Usa o fallback
        }

        const selectedType = $select.val();
        const typesWithOptions = ['UNICA_ESCOLHA', 'MULTIPLA_ESCOLHA'];
        const shouldShow = typesWithOptions.includes(selectedType);

        console.log(`[QAdmin V16] Toggle: Row=${rowId}, Type=${selectedType}, ShouldShow=${shouldShow}`);
        // Força show/hide
        optionsContainer.toggle(shouldShow);
    }

    // --- Execução Principal ---
    $(document).ready(function() {
        console.log("[QAdmin V16] Document Ready");

        // Aplica toggle inicial aos elementos já presentes
        function runInitialToggle() {
            console.log("[QAdmin V16] Applying initial toggle logic...");
            let count = 0;
             // Seleciona TODOS os selects de tipo_resposta que NÃO estão no template vazio
             $('select[name$="-tipo_resposta"]').not('.djn-empty-form select').each(function() {
                 toggleOptions(this); // Passa o elemento select diretamente
                 count++;
            });
             console.log(`[QAdmin V16] Initial toggle logic applied to ${count} selects.`);
        }
        // Roda APÓS um delay significativo
        setTimeout(runInitialToggle, 1500); // 1.5 segundos


        // Ouve a mudança em QUALQUER select de tipo_resposta
        $(document).on('change', 'select[name$="-tipo_resposta"]', function() {
             console.log("[QAdmin V16] Select change detected");
             toggleOptions(this); // 'this' é o elemento select que mudou
        });

        // REMOVIDO: Listener para formset:added (vamos focar no change)
        // REMOVIDO: Lógica de placeholders
        // REMOVIDO: Lógica de renomear botões

    }); // Fim Document Ready

})(django.jQuery); // Passa django.jQuery como '$'