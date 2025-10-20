(function($) { // '$' é django.jQuery
    console.log("[QAdmin V17 - Toggle Focus] Script loaded.");

    // Função toggleOptions (Busca a partir do select)
    function toggleOptions(selectElement) {
        const $select = $(selectElement);
        // 1. Sobe para a linha da tabela (TR) que contém a pergunta
        const $questionRow = $select.closest('tr'); // O TR pai mais próximo

        if (!$questionRow.length) {
            console.error("[QAdmin V17] Toggle: Could not find parent TR for select:", $select.attr('name'));
            return;
        }
        const rowId = $questionRow.attr('id') || $questionRow.index(); // Pega ID ou índice

        // 2. Tenta achar o container de opções DENTRO dessa linha TR
        //    nested_admin geralmente coloca o formset aninhado (opções) dentro de uma célula TD
        //    e dentro dela há um .inline-group
        const optionsContainer = $questionRow.find('td .inline-group').first(); // Pega o PRIMEIRO .inline-group dentro de qualquer TD

        if (!optionsContainer.length) {
            console.warn(`[QAdmin V17] Toggle: Options Container (.inline-group) not found within row ${rowId}. Cannot toggle.`);
            return; // Sai se não achar o container das opções
        }

        const selectedType = $select.val();
        const typesWithOptions = ['UNICA_ESCOLHA', 'MULTIPLA_ESCOLHA'];
        const shouldShow = typesWithOptions.includes(selectedType);

        console.log(`[QAdmin V17] Toggle: Row=${rowId}, Type=${selectedType}, ShouldShow=${shouldShow}`);
        // Força show/hide no container encontrado
        optionsContainer.toggle(shouldShow);
    }

    // --- Execução Principal ---
    $(document).ready(function() {
        console.log("[QAdmin V17] Document Ready");

        // Aplica toggle inicial a TODAS as perguntas existentes
        function runInitialToggle() {
            console.log("[QAdmin V17] Applying initial toggle logic...");
            let count = 0;
             // Seleciona TODOS os selects de tipo_resposta visíveis (não do template vazio)
             $('tr:not(.djn-empty-form) select[name$="-tipo_resposta"]').each(function() {
                 try {
                     toggleOptions(this); // Passa o elemento select diretamente
                     count++;
                 } catch (e) {
                     console.error("[QAdmin V17] Error during initial toggle:", e, "on select:", $(this).attr('name'));
                 }
            });
             console.log(`[QAdmin V17] Initial toggle logic attempted on ${count} selects.`);
        }
        // Roda APÓS um delay maior para dar chance ao nested_admin
        setTimeout(runInitialToggle, 2000); // 2 segundos


        // Ouve a mudança em QUALQUER select de tipo_resposta usando event delegation
        // Usa 'body' para garantir que funcione para selects adicionados dinamicamente
        $('body').on('change', 'select[name$="-tipo_resposta"]', function() {
             console.log("[QAdmin V17] Select change detected");
             try {
                 toggleOptions(this); // 'this' é o elemento select que mudou
             } catch (e) {
                  console.error("[QAdmin V17] Error during change toggle:", e, "on select:", $(this).attr('name'));
             }
        });

        // REMOVIDO: Listener para formset:added
        // REMOVIDO: Lógica de placeholders
        // REMOVIDO: Lógica de renomear botões

    }); // Fim Document Ready

})(django.jQuery); // Passa django.jQuery como '$'