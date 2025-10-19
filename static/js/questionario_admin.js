(function($) { // '$' é django.jQuery
    console.log("[QAdmin V15] Script loaded.");

    // Função toggleOptions (Busca elementos a partir do select)
    function toggleOptions(selectElement) {
        const $select = $(selectElement);
        // Sobe para a linha da tabela (TR) que contém esta pergunta
        // nested_admin geralmente coloca inlines dentro de TRs com classe 'dynamic-<prefix>'
        const $questionRow = $select.closest('tr[class*="dynamic-perguntas_set"]'); // Busca TR pai com classe que começa com 'dynamic-perguntas_set'

        if (!$questionRow.length) {
            console.error("[QAdmin V15] Toggle: Could not find parent TR for select:", $select.attr('name'));
            return;
        }

        const rowId = $questionRow.attr('id') || $questionRow.index();
        console.log(`[QAdmin V15] toggleOptions called for row: ${rowId}`);

        // Tenta achar o container de opções DENTRO da linha da pergunta
        // Geralmente está dentro de uma célula TD e depois num .inline-group
        const optionsContainer = $questionRow.find('td .inline-group'); // Busca genérica por .inline-group dentro de qualquer TD da linha

        if (!optionsContainer.length) {
            console.warn(`[QAdmin V15] Toggle: Options Container (.inline-group) not found in ${rowId}`); return;
        }

        const selectedType = $select.val();
        const typesWithOptions = ['UNICA_ESCOLHA', 'MULTIPLA_ESCOLHA'];
        const shouldShow = typesWithOptions.includes(selectedType);

        console.log(`[QAdmin V15] Toggle: Row=${rowId}, Type=${selectedType}, ShouldShow=${shouldShow}`);
        // Força show/hide
        optionsContainer.toggle(shouldShow);
    }

    // --- Execução Principal ---
    $(document).ready(function() {
        console.log("[QAdmin V15] Document Ready");

        // Aplica toggle inicial a TODAS as perguntas existentes na página
        function runInitialToggle() {
            console.log("[QAdmin V15] Applying initial toggle logic...");
            let count = 0;
             $('tr[class*="dynamic-perguntas_set"]').not('.djn-empty-form').each(function() {
                 // Encontra o select DENTRO desta linha e chama o toggle
                 const $select = $(this).find('select[name$="-tipo_resposta"]');
                 if ($select.length) {
                    toggleOptions($select[0]); // Passa o elemento DOM do select
                    count++;
                 } else {
                     console.warn("[QAdmin V15] Initial Toggle: Select not found in row:", $(this).attr('id'));
                 }
            });
             console.log(`[QAdmin V15] Initial toggle logic applied to ${count} questions.`);
        }
        // Roda APÓS um delay significativo para garantir que nested_admin montou o DOM
        setTimeout(runInitialToggle, 1500); // 1.5 segundos


        // Ouve a mudança em QUALQUER select de tipo_resposta que apareça na página
        // Usa event delegation no 'document' para pegar elementos futuros
        $(document).on('change', 'select[name$="-tipo_resposta"]', function() {
             console.log("[QAdmin V15] Select change detected");
             toggleOptions(this); // 'this' é o elemento select que mudou
        });

        // REMOVIDO: Listener para formset:added
        // REMOVIDO: Lógica de placeholders
        // REMOVIDO: Lógica de renomear botões

    }); // Fim Document Ready

})(django.jQuery); // Passa django.jQuery como '$'