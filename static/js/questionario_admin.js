(function($) {
    // Função que mostra ou esconde o bloco de "Opções"
    function toggleOptions(row) {
        // Garante que 'row' é um objeto jQuery
        const $row = $(row);
        const selectElement = $row.find('.field-tipo_resposta select');
        const optionsBlock = $row.find('.inline-group'); // O bloco de Opções

        // Verifica se os elementos foram encontrados (debug)
        if (!selectElement.length) {
            console.warn("Select de tipo_resposta não encontrado na linha:", $row);
            return;
        }
         if (!optionsBlock.length) {
            console.warn("Bloco de opções (.inline-group) não encontrado na linha:", $row);
            // Mesmo que não ache, continua para o resto da lógica (placeholder etc)
        }

        const selectedType = selectElement.val();
        const typesWithOptions = ['UNICA_ESCOLHA', 'MULTIPLA_ESCOLHA'];

        if (typesWithOptions.includes(selectedType)) {
             // Só mostra se for um tipo com opções
            optionsBlock.slideDown();
        } else {
            // Esconde para todos os outros tipos (Texto, Escala)
            optionsBlock.slideUp();
        }
    }

    // Função para adicionar placeholder
    function addPlaceholder(row) {
        const $row = $(row);
        const questionInput = $row.find('.field-texto_pergunta input[type="text"]');
        if (questionInput.length > 0 && !questionInput.attr('placeholder')) {
            questionInput.attr('placeholder', 'Pergunta');
        }
    }

    $(document).ready(function() {

        // Renomeia os botões
        setInterval(function() {
            $('.djn-add-item a').each(function() {
                const $button = $(this);
                if ($button.text().includes('Opcao Resposta')) {
                    $button.text('Adicionar Opção de Resposta');
                }
                // Ajuste para pegar "Pergunta" mas não "Opcao Resposta"
                if ($button.text().includes('Pergunta') && !$button.text().includes('Opcao')) {
                    $button.text('Adicionar Pergunta');
                }
            });
        }, 500);

        // Ouve a mudança no dropdown "Tipo de Resposta"
        // Usa 'body' para garantir que funcione em elementos adicionados dinamicamente
        $('body').on('change', '#perguntas-group .field-tipo_resposta select', function() {
            const row = $(this).closest('.inline-related');
            toggleOptions(row);
        });

        // Ouve a adição de uma nova pergunta
        $(document).on('djnesting:added', function(event, inline) {
            // Verifica se é um inline de 'pergunta'
            if (inline.prefix.includes('pergunta')) {
                // --- CORREÇÃO: Garante que as opções comecem escondidas ---
                 const newRow = inline.row;
                 const optionsBlock = newRow.find('.inline-group');
                 if (optionsBlock.length) {
                    optionsBlock.hide(); // Começa escondido
                 }
                // Roda o toggleOptions para garantir consistência inicial
                toggleOptions(newRow);
                addPlaceholder(newRow);
            }
        });

        // Roda as funções para as perguntas já existentes ao carregar
        // Aumenta o timeout levemente para garantir que o DOM esteja pronto
        setTimeout(function() {
            $('#perguntas-group .inline-related').each(function() {
                const $row = $(this);
                toggleOptions($row); // Esconde/mostra opções conforme o tipo
                addPlaceholder($row); // Adiciona placeholder
            });
        }, 250); // Aumentado para 250ms
    });
})(django.jQuery);