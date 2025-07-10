require('dotenv').config(); const axios = require('axios'); const { ethers } = require('ethers'); const TelegramBot = require('node-telegram-bot-api');

// === ENV === const INFURA_URL = process.env.INFURA_URL; const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN; const TELEGRAM_CHAT_ID = process.env.TELEGRAM_CHAT_ID; const MAIN_WALLET_PK = process.env.WALLET_MAIN_PK; const ROTATING_WALLETS = [ process.env.WALLET_1_PK, process.env.WALLET_2_PK ];

// === CONFIG === const INTERVAL_SECONDS = 20; const TRADE_AMOUNT_ETH = '0.001'; // customizable const ZEROX_API = 'https://api.0x.org';

// === SETUP === const provider = new ethers.providers.JsonRpcProvider(INFURA_URL); const bot = new TelegramBot(TELEGRAM_BOT_TOKEN, { polling: true });

const wallets = ROTATING_WALLETS.map(pk => new ethers.Wallet(pk, provider)); const mainWallet = new ethers.Wallet(MAIN_WALLET_PK, provider); let autoTrading = true; let tokenAddress = ''; let isBuying = true;

// === UTILS === async function getETHBalance(address) { const balance = await provider.getBalance(address); return ethers.utils.formatEther(balance); }

async function get0xQuote(buy, sell, amount) { try { const url = ${ZEROX_API}/swap/v1/quote; const params = { sellToken: buy, buyToken: sell, sellAmount: amount }; const res = await axios.get(url, { params }); return res.data; } catch (err) { console.error('❌ Quote error:', err.message); return null; } }

async function executeSwap(wallet, quote) { try { const tx = { to: quote.to, data: quote.data, value: ethers.BigNumber.from(quote.value), gasLimit: quote.gas || 200000 }; const sent = await wallet.sendTransaction(tx); await sent.wait(); return sent.hash; } catch (err) { console.error('❌ Swap error:', err.message); return null; } }

async function sendBuy() { const wallet = wallets[Math.floor(Math.random() * wallets.length)]; const ethAmount = ethers.utils.parseEther(TRADE_AMOUNT_ETH).toString(); const quote = await get0xQuote('ETH', tokenAddress, ethAmount); if (!quote) return bot.sendMessage(TELEGRAM_CHAT_ID, '❌ Buy quote failed');

const txHash = await executeSwap(wallet, quote); if (txHash) { bot.sendMessage(TELEGRAM_CHAT_ID, ✅ Buy tx: https://etherscan.io/tx/${txHash}); } }

async function sendSell() { const wallet = wallets[Math.floor(Math.random() * wallets.length)]; const tokenBal = await getTokenBalance(wallet.address, tokenAddress); if (tokenBal === '0') return bot.sendMessage(TELEGRAM_CHAT_ID, '❌ No tokens to sell');

const quote = await get0xQuote(tokenAddress, 'ETH', tokenBal); if (!quote) return bot.sendMessage(TELEGRAM_CHAT_ID, '❌ Sell quote failed');

const txHash = await executeSwap(wallet, quote); if (txHash) { bot.sendMessage(TELEGRAM_CHAT_ID, ✅ Sell tx: https://etherscan.io/tx/${txHash}); } }

async function getTokenBalance(walletAddr, tokenAddr) { const erc20 = new ethers.Contract( tokenAddr, ["function balanceOf(address) view returns (uint256)"], provider ); const bal = await erc20.balanceOf(walletAddr); return bal.toString(); }

// === LOOP === async function autoTradeLoop() { if (!autoTrading || !tokenAddress) return; if (isBuying) await sendBuy(); else await sendSell(); isBuying = !isBuying; setTimeout(autoTradeLoop, INTERVAL_SECONDS * 1000); }

// === TELEGRAM === bot.onText(//revive (.+)/, (msg, match) => { tokenAddress = match[1]; bot.sendMessage(msg.chat.id, 🚀 Pump started for ${tokenAddress}); autoTrading = true; autoTradeLoop(); });

bot.onText(//sell all/, async () => { for (const wallet of wallets) { const bal = await getTokenBalance(wallet.address, tokenAddress); if (bal !== '0') { const quote = await get0xQuote(tokenAddress, 'ETH', bal); if (quote) { const tx = await executeSwap(wallet, quote); if (tx) bot.sendMessage(TELEGRAM_CHAT_ID, 💣 Sold all from ${wallet.address}\nhttps://etherscan.io/tx/${tx}); } } } });

bot.onText(//status/, async () => { const bal = await getETHBalance(mainWallet.address); bot.sendMessage(TELEGRAM_CHAT_ID, 📊 Main Wallet: ${mainWallet.address}\nETH: ${bal}\nTarget Token: ${tokenAddress}\nTrading: ${autoTrading}); });

bot.onText(//stop/, () => { autoTrading = false; bot.sendMessage(TELEGRAM_CHAT_ID, '🛑 Auto-trading stopped.'); });

bot.onText(//start/, () => { if (!tokenAddress) return bot.sendMessage(TELEGRAM_CHAT_ID, '⚠️ Use /revive <token> first'); autoTrading = true; bot.sendMessage(TELEGRAM_CHAT_ID, '▶️ Auto-trading resumed.'); autoTradeLoop(); });

￼Enter
