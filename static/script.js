document.addEventListener('DOMContentLoaded', (event) => {
    // Função para habilitar ou desabilitar os campos do formulário com base na seleção da loja
    window.enableForm = function() {
        const store = document.getElementById('store').value;
        const material = document.getElementById('material');
        const quantity = document.getElementById('quantity');
        const description = document.getElementById('description'); // Garantindo que description também seja acessível
        const buttons = document.querySelectorAll('button');

        if (store) {
            material.disabled = false;
            quantity.disabled = false;
            buttons.forEach(button => button.disabled = false);
        } else {
            material.disabled = true;
            quantity.disabled = true;
            buttons.forEach(button => button.disabled = true);
        }
    };
    
    // Função para resetar o formulário e reabilitar os campos conforme necessário
    function cancelOrder() {
        document.getElementById('orderForm').reset();
        enableForm(); 
    }

    // Adiciona o evento de mudança ao campo material para buscar a descrição e atualizar a autorização
    if (document.getElementById('material')) {
        document.getElementById('material').addEventListener('change', updateDescription);
    }

    // Função para buscar a descrição do material e atualizar a autorização
    function updateDescription() {
        const material = document.getElementById('material').value;
    
        fetch(`/get-description?material=${material}`)
            .then(response => response.json())
            .then(data => {
                document.getElementById('description').value = data.description; 
                const submit = document.getElementById('submit'); 
                if (data.authorized) {
                    submit.disabled = false;
                } else {
                    alert('Material não autorizado.');
                    submit.disabled = true;
                }
            })
            .catch(error => console.log('Erro ao buscar descrição:', error));
    }

    
    const form = document.querySelector('form');
    form.addEventListener('submit', function() {
       
        document.getElementById('loadingModal').style.display = "block";
        setTimeout(function() {
            document.getElementById('loadingModal').style.display = "none";
        }, 10000); 
    });
});
