document.addEventListener('DOMContentLoaded', () => {
    const connectBtn = document.getElementById('connectWalletBtn');
    const walletAddressSpan = document.getElementById('walletAddress');

    // Comprobar si MetaMask está instalado
    if (typeof window.ethereum !== 'undefined') {
        console.log('MetaMask está instalado!');
    } else {
        console.log('Por favor, instala MetaMask.');
        if (connectBtn) {
            connectBtn.innerText = 'MetaMask no encontrado';
            connectBtn.disabled = true;
        }
        return;
    }

    connectBtn.addEventListener('click', async () => {
        try {
            // Solicitar acceso a las cuentas del usuario
            const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
            const account = accounts[0];
            
            // Mostrar la dirección acortada en la interfaz
            const shortenedAddress = `${account.substring(0, 6)}...${account.substring(account.length - 4)}`;
            walletAddressSpan.innerText = `Conectado: ${shortenedAddress}`;
            connectBtn.innerText = 'Conectado';
            connectBtn.classList.remove('btn-primary');
            connectBtn.classList.add('btn-success');

            console.log('Cuenta conectada:', account);

            // Opcional: Puedes enviar esta dirección a tu backend en Flask si necesitas registrar la sesión
            // registrarUsuarioEnBackend(account);

        } catch (error) {
            console.error('Usuario rechazó la conexión o ocurrió un error:', error);
        }
    });

    // Opcional: Detectar si el usuario cambia de cuenta en MetaMask
    window.ethereum.on('accountsChanged', (accounts) => {
        if (accounts.length > 0) {
            const account = accounts[0];
            const shortenedAddress = `${account.substring(0, 6)}...${account.substring(account.length - 4)}`;
            walletAddressSpan.innerText = `Conectado: ${shortenedAddress}`;
        } else {
            walletAddressSpan.innerText = '';
            connectBtn.innerText = 'Conectar MetaMask';
            connectBtn.classList.remove('btn-success');
            connectBtn.classList.add('btn-primary');
        }
    });
});