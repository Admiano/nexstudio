#!/usr/bin/env python3
"""Domain entity-bank builder: crypto + AI vocabulary for the explainer styles.

Adds curated domain terms to ``entity_bank`` in ``styles.json`` and writes
``entity_phrases`` — the surface-form map (aliases + multi-word phrases) that
``make_reel.pick_entities`` resolves before single-word matching.

Every ``colour``/``mono``/``emoji`` ref is validated against the vendored
community registries (``assets/community/icons-registry.json`` and
``colour-registry.json``); a missing ref fails the build. Entries may leave a
family unset to be auto-resolved: the resolver searches asset labels/tags with
a pack-preference order and reports what it picked so garbage matches get
explicit overrides instead of shipping silently.

    python3 tools/build_domain_bank.py            # write styles.json
    python3 tools/build_domain_bank.py --report   # print resolved table only
"""
import argparse, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMUNITY = ROOT / "assets" / "community"
STYLES = ROOT / "styles.json"

# ---------------------------------------------------------------------------
# Vocabulary: canonical key -> {colour, mono, emoji, photo, aliases}
#   colour/mono/emoji: explicit registry ids, or AUTO to resolve, or None.
#   photo:  free-form concept string for the lexicon photo rung.
#   aliases: extra surface forms -> phrase map entries (incl. multi-word).
# ---------------------------------------------------------------------------

CRYPTO = {
    # --- coins & tokens (brand logos where available) ---
    "bitcoin":        {"colour": "brand.si.bitcoin", "mono": "icon.mingcute.currency-bitcoin-line", "emoji": "emoji.noto.coin", "photo": "bitcoin", "aliases": ["btc", "₿", "bitcoins"]},
    "ethereum":       {"colour": "brand.si.ethereum", "mono": "icon.tabler.currency-ethereum", "emoji": "emoji.noto.diamond-with-a-dot", "photo": "ethereum", "aliases": ["eth", "ether", "ethereum's"]},
    "tether":         {"colour": "brand.si.tether", "photo": "tether usdt", "aliases": ["usdt"]},
    "usdc":           {"photo": "usd coin", "emoji": "emoji.noto.dollar-banknote", "aliases": ["usd coin", "usdcoin"]},
    "solana":         {"colour": "brand.si.solana", "photo": "solana", "aliases": ["sol"]},
    "cardano":        {"colour": "brand.logos.cardano", "photo": "cardano", "aliases": ["ada"]},
    "dogecoin":       {"colour": "brand.si.dogecoin", "mono": "icon.tabler.currency-dogecoin", "photo": "dogecoin", "aliases": ["doge"]},
    "xrp":            {"colour": "brand.si.xrp", "photo": "xrp", "aliases": ["ripple labs", "ripple xrp", "xrp ledger"]},
    "binance":        {"colour": "brand.si.binance", "mono": "icon.mingcute.binance-coin-bnb-line", "photo": "binance", "aliases": ["bnb", "binance coin", "bnb chain"]},
    "litecoin":       {"colour": "brand.si.litecoin", "photo": "litecoin", "aliases": ["ltc"]},
    "monero":         {"colour": "brand.logos.monero", "mono": "icon.tabler.coin-monero", "photo": "monero", "aliases": ["xmr"]},
    "polkadot":       {"colour": "brand.si.polkadot", "photo": "polkadot", "aliases": ["dot token", "polkadot chain"]},
    "avalanche":      {"emoji": "emoji.noto.snow-capped-mountain", "photo": "avalanche crypto", "aliases": ["avax"]},
    "chainlink":      {"colour": "brand.si.chainlink", "photo": "chainlink", "aliases": ["link token", "chainlink oracle"]},
    "tron":           {"photo": "tron crypto", "aliases": ["trx"]},
    "stellar":        {"colour": "brand.si.stellar", "photo": "stellar crypto", "aliases": ["xlm"]},
    "nearprotocol":   {"colour": "brand.si.near", "photo": "near protocol", "aliases": ["near protocol", "nearprotocol", "near chain", "near blockchain"]},
    "aptos":          {"photo": "aptos", "aliases": ["aptos chain"]},
    "sui":            {"colour": "brand.si.sui", "photo": "sui blockchain", "aliases": []},
    "arbitrum":       {"photo": "arbitrum", "aliases": ["arb"]},
    "optimism":       {"colour": "brand.si.optimism", "photo": "optimism rollup", "aliases": ["op mainnet", "op stack", "optimism chain"]},
    "polygon":        {"colour": "brand.si.polygon", "photo": "polygon matic", "aliases": ["matic", "polygon matic"]},
    "cosmos":         {"photo": "cosmos atom", "aliases": ["cosmos hub", "cosmos atom", "cosmos network", "atom coin"]},
    "algorand":       {"colour": "brand.si.algorand", "photo": "algorand", "aliases": ["algo token"]},
    "shiba":          {"photo": "shiba inu coin", "emoji": "emoji.noto.dog", "aliases": ["shib", "shiba inu"]},
    "pepe":           {"emoji": "emoji.noto.frog", "photo": "pepe coin", "aliases": ["pepe coin"]},
    "bitcoincash":    {"colour": "brand.si.bitcoincash", "photo": "bitcoin cash", "aliases": ["bitcoin cash", "bch"]},
    "zcash":          {"colour": "brand.si.zcash", "photo": "zcash", "aliases": ["zec"]},
    "dashcoin":       {"colour": "brand.si.dash", "photo": "dash crypto", "aliases": ["dash coin", "dash crypto", "dash token"]},
    "iota":           {"colour": "brand.si.iota", "photo": "iota", "aliases": []},
    "hedera":         {"colour": "brand.si.hedera", "photo": "hedera hashgraph", "aliases": ["hbar", "hashgraph"]},
    "fantom":         {"colour": "brand.si.fantom", "photo": "fantom", "aliases": ["ftm"]},
    "decentraland":   {"colour": "brand.si.decentraland", "photo": "decentraland", "aliases": ["mana"]},
    "ethereumclassic": {"photo": "ethereum classic", "aliases": ["ethereum classic", "etc"]},
    "tezos":          {"photo": "tezos", "aliases": ["xtz"]},
    "eos":            {"photo": "eos crypto", "aliases": []},
    "toncoin":        {"photo": "toncoin", "aliases": ["ton", "ton coin"]},
    "memecoin":       {"emoji": "emoji.noto.frog", "mono": "icon.mingcute.coin-line", "photo": "meme coin", "aliases": ["meme coin", "memecoins", "meme coins"]},
    "stablecoin":     {"emoji": "emoji.noto.dollar-banknote", "mono": "icon.mingcute.coin-2-line", "photo": "stablecoin", "aliases": ["stablecoins", "stable coin", "stable coins"]},
    "altcoin":        {"mono": "icon.mingcute.coin-3-line", "emoji": "emoji.noto.coin", "photo": "altcoins", "aliases": ["altcoins", "alt coin", "alt coins"]},
    "token":          {"mono": "icon.mingcute.coin-line", "emoji": "emoji.noto.coin", "photo": "crypto token", "aliases": ["tokens"]},
    "coin":           {"mono": "icon.mingcute.coin-line", "emoji": "emoji.noto.coin", "photo": "coin", "aliases": ["coins"]},
    "cryptocurrency": {"colour": "icon.icon-park-color.bitcoin", "mono": "icon.mingcute.currency-bitcoin-line", "emoji": "emoji.noto.coin", "photo": "cryptocurrency", "aliases": ["crypto", "cryptocurrencies", "cryptos"]},
    # --- core concepts ---
    "blockchain":     {"mono": "icon.carbon.chart-network", "emoji": "emoji.noto.chains", "colour": "icon.icon-park-color.blockchain", "photo": "blockchain", "aliases": ["blockchains", "block chain"]},
    "wallet":         {"mono": "icon.ant-design.wallet-outlined", "emoji": "emoji.noto.handbag", "colour": "icon.icon-park-color.wallet", "photo": "crypto wallet", "aliases": ["wallets", "digital wallet", "crypto wallet", "web3 wallet"]},
    "coldwallet":     {"mono": "icon.carbon.bank-vault", "emoji": "emoji.noto.locked", "photo": "hardware wallet", "aliases": ["cold wallet", "cold storage", "hardware wallet", "hardware wallets", "cold wallets"]},
    "hotwallet":      {"emoji": "emoji.noto.mobile-phone", "photo": "mobile crypto wallet", "aliases": ["hot wallet", "hot wallets", "mobile wallet", "software wallet"]},
    "seedphrase":     {"mono": "icon.icon-park-outline.key", "emoji": "emoji.noto.key", "photo": "seed phrase backup", "aliases": ["seed phrase", "seed phrases", "recovery phrase", "recovery phrases", "seed words", "backup phrase", "secret phrase", "mnemonic", "mnemonic phrase", "12 words", "twelve words", "24 words"]},
    "privatekey":     {"mono": "icon.carbon.api-key", "emoji": "emoji.noto.old-key", "photo": "private key", "aliases": ["private key", "private keys", "secret key"]},
    "publickey":      {"mono": "icon.carbon.key", "emoji": "emoji.noto.key", "photo": "public key", "aliases": ["public key", "public keys"]},
    "address":        {"mono": "icon.carbon.qr-code", "emoji": "emoji.noto.identification-card", "photo": "wallet address", "aliases": ["wallet address", "addresses", "crypto address", "deposit address", "receiving address"]},
    "ledger":         {"emoji": "emoji.noto.ledger", "mono": "icon.ant-design.account-book-outlined", "photo": "ledger book", "aliases": ["distributed ledger", "ledgers", "the ledger"]},
    "smartcontract":  {"mono": "icon.icon-park-outline.edit-name", "emoji": "emoji.noto.memo", "photo": "smart contract", "aliases": ["smart contract", "smart contracts", "contract code"]},
    "defi":           {"emoji": "emoji.noto.bank", "mono": "icon.icon-park-outline.exchange", "photo": "decentralized finance", "aliases": ["decentralized finance", "decentralised finance", "open finance"]},
    "nft":            {"emoji": "emoji.noto.framed-picture", "mono": "icon.icon-park-outline.picture-album", "photo": "nft art", "aliases": ["nfts", "non-fungible token", "non-fungible tokens", "digital collectible", "digital collectibles", "nft collection", "nft collections"]},
    "mint":           {"mono": "icon.ant-design.file-add-outlined", "emoji": "emoji.noto.sparkles", "photo": "minting nft", "aliases": ["minting", "minted", "mints", "nft mint", "token mint"]},
    "gas":            {"emoji": "emoji.noto.fuel-pump", "colour": "emoji.noto.fuel-pump", "mono": "icon.lucide.bolt", "photo": "gas fee", "aliases": ["gas fee", "gas fees", "gas price", "gas cost", "gas costs", "transaction fee", "transaction fees", "network fee", "network fees"]},
    "gwei":           {"photo": "gwei", "aliases": []},
    "transaction":    {"emoji": "emoji.noto.left-right-arrow", "mono": "icon.icon-park-outline.exchange-four", "photo": "crypto transaction", "aliases": ["transactions", "tx", "txns", "crypto transaction"]},
    "block":          {"emoji": "emoji.noto.package", "photo": "blockchain block", "aliases": ["blocks", "new block"]},
    "mining":         {"emoji": "emoji.noto.pick", "mono": "icon.lucide.hammer" , "photo": "crypto mining", "aliases": ["mine", "mined", "crypto mining", "bitcoin mining", "mining rig", "mining rigs"]},
    "miner":          {"emoji": "emoji.noto.pick", "photo": "crypto miner", "aliases": ["miners"]},
    "hashrate":       {"photo": "hashrate", "aliases": ["hash rate", "hash power"]},
    "proofofwork":    {"emoji": "emoji.noto.hammer-and-pick", "photo": "proof of work", "aliases": ["proof of work", "pow"]},
    "proofofstake":   {"emoji": "emoji.noto.balance-scale", "photo": "proof of stake", "aliases": ["proof of stake", "pos"]},
    "staking":        {"mono": "icon.carbon.bank-vault", "emoji": "emoji.noto.money-bag", "colour": "emoji.noto.money-bag", "photo": "crypto staking", "aliases": ["stake", "staked", "stakes", "stake your", "staking rewards", "restaking", "liquid staking", "staking pool"]},
    "validator":      {"emoji": "emoji.noto.check-mark-button", "photo": "blockchain validator", "aliases": ["validators", "validator node"]},
    "node":           {"mono": "icon.carbon.network-3", "emoji": "emoji.noto.globe-with-meridians", "photo": "network node", "aliases": ["nodes", "full node", "validator node", "network node"]},
    "consensus":      {"emoji": "emoji.noto.handshake", "photo": "consensus mechanism", "aliases": ["consensus mechanism", "consensus algorithm"]},
    "dao":            {"emoji": "emoji.noto.handshake", "photo": "dao governance", "aliases": ["daos", "decentralized autonomous organization", "decentralised autonomous organisation"]},
    "dapp":           {"emoji": "emoji.noto.mobile-phone", "photo": "decentralized app", "aliases": ["dapps", "decentralized app", "decentralized apps", "decentralized application"]},
    "dex":            {"mono": "icon.icon-park-outline.exchange", "emoji": "emoji.noto.left-right-arrow", "photo": "decentralized exchange", "aliases": ["decentralized exchange", "decentralised exchange", "dexes", "on-chain exchange"]},
    "cex":            {"emoji": "emoji.noto.bank", "photo": "centralized exchange", "aliases": ["centralized exchange", "centralised exchange", "cexes"]},
    "exchange":       {"mono": "icon.icon-park-outline.exchange", "emoji": "emoji.noto.left-right-arrow", "photo": "crypto exchange", "aliases": ["exchanges", "crypto exchange", "crypto exchanges", "trading platform", "trading platforms"]},
    "liquidity":      {"emoji": "emoji.noto.droplet", "photo": "liquidity pool", "aliases": ["liquidity pool", "liquidity pools", "liquidity provision", "lp", "liquid market"]},
    "yieldfarming":   {"emoji": "emoji.noto.ear-of-corn", "photo": "yield farming", "aliases": ["yield farming", "yield farm", "farming", "liquidity mining"]},
    "apy":            {"emoji": "emoji.noto.chart-increasing", "photo": "apy percentage", "aliases": ["apr", "annual percentage yield", "yield"]},
    "lending":        {"emoji": "emoji.noto.money-with-wings", "photo": "crypto lending", "aliases": ["lend", "borrowing", "borrow", "crypto lending", "loans", "flash loan", "flash loans"]},
    "oracle":         {"emoji": "emoji.noto.crystal-ball", "photo": "blockchain oracle", "aliases": ["oracles", "price oracle", "blockchain oracle", "chainlink oracle"]},
    "bridge":         {"emoji": "emoji.noto.rainbow", "photo": "blockchain bridge", "aliases": ["bridges", "bridging", "cross-chain", "cross chain", "blockchain bridge", "token bridge"]},
    "layer1":         {"emoji": "emoji.noto.books", "photo": "layer 1 blockchain", "aliases": ["layer 1", "layer one", "l1", "base layer"]},
    "layer2":         {"emoji": "emoji.noto.books", "photo": "layer 2 scaling", "aliases": ["layer 2", "l2", "layer two", "scaling solution", "scaling solutions"]},
    "rollup":         {"emoji": "emoji.noto.roll-of-paper", "photo": "rollup", "aliases": ["rollups", "zk rollup", "zk-rollup", "optimistic rollup", "zk rollups"]},
    "sidechain":      {"photo": "sidechain", "aliases": ["sidechains", "side chain"]},
    "mainnet":        {"emoji": "emoji.noto.globe-with-meridians", "photo": "mainnet launch", "aliases": ["main net", "mainnets", "mainnet launch", "mainnet launch"]},
    "testnet":        {"emoji": "emoji.noto.test-tube", "photo": "testnet", "aliases": ["test net", "testnets", "test network"]},
    "tokenomics":     {"emoji": "emoji.noto.bar-chart", "photo": "tokenomics", "aliases": ["token economics", "supply schedule", "emission schedule"]},
    "whitepaper":     {"emoji": "emoji.noto.page-facing-up", "photo": "whitepaper", "aliases": ["white paper", "litepaper", "lite paper", "technical paper"]},
    "ico":            {"emoji": "emoji.noto.money-bag", "photo": "token sale", "aliases": ["initial coin offering", "token sale", "token sales", "ido", "ieo", "initial dex offering", "presale", "pre-sale", "token launch", "launchpad"]},
    "airdrop":        {"emoji": "emoji.noto.wrapped-gift", "photo": "airdrop", "aliases": ["airdrops", "token airdrop", "free tokens"]},
    "marketcap":      {"emoji": "emoji.noto.bar-chart", "mono": "icon.ant-design.pie-chart-outlined", "photo": "market cap", "aliases": ["market cap", "market capitalization", "market capitalisation", "mcap", "fully diluted", "fdv"]},
    "volume":         {"emoji": "emoji.noto.bar-chart", "photo": "trading volume", "aliases": ["trading volume", "24h volume", "daily volume"]},
    "candlestick":    {"mono": "icon.tabler.chart-candle", "emoji": "emoji.noto.bar-chart", "colour": "icon.fluent-color.data-trending-48", "photo": "candlestick chart", "aliases": ["candlestick chart", "candlesticks", "candle chart", "candles", "price chart", "price action"]},
    "bullmarket":     {"emoji": "emoji.noto.chart-increasing", "colour": "icon.icon-park-color.stock-market", "photo": "bull market", "aliases": ["bull market", "bull run", "bullish", "uptrend", "pumping", "to the moon"]},
    "bearmarket":     {"emoji": "emoji.noto.bear", "photo": "bear market", "aliases": ["bear market", "bearish", "downtrend", "dumping", "red market"]},
    "whale":          {"emoji": "emoji.noto.whale", "mono": "icon.lucide.fish" , "photo": "crypto whale", "aliases": ["whales", "crypto whale", "big holder"]},
    "hodl":           {"emoji": "emoji.noto.gem-stone", "photo": "hodl", "aliases": ["hodling", "hodler", "hodlers", "hold", "holding", "long-term hold", "diamond hands"]},
    "fomo":           {"emoji": "emoji.noto.alarm-clock", "photo": "fomo", "aliases": ["fear of missing out"]},
    "fud":            {"emoji": "emoji.noto.warning", "photo": "fud fear doubt", "aliases": ["fear uncertainty doubt", "fear uncertainty and doubt"]},
    "mooning":        {"emoji": "emoji.noto.full-moon", "photo": "mooning crypto", "aliases": ["moon", "mooned", "moons", "when moon", "lambo"]},
    "rekt":           {"emoji": "emoji.noto.chart-decreasing", "photo": "rekt trader", "aliases": ["wrecked", "got rekt"]},
    "paperhands":     {"emoji": "emoji.noto.raising-hands", "photo": "paper hands", "aliases": ["paper hands", "weak hands", "panic sell", "panic selling"]},
    "rugpull":        {"emoji": "emoji.noto.warning", "mono": "icon.ant-design.warning-outlined", "photo": "rug pull scam", "aliases": ["rug pull", "rug pulls", "rugged", "exit scam", "rugpull"]},
    "scam":           {"emoji": "emoji.noto.warning", "mono": "icon.ant-design.warning-outlined", "photo": "crypto scam", "aliases": ["scams", "scammer", "fraud", "ponzi", "ponzi scheme", "phishing", "honey pot"]},
    "hack":           {"emoji": "emoji.noto.skull-and-crossbones", "mono": "icon.icon-park-outline.bug", "photo": "crypto hack", "aliases": ["hacked", "hacker", "hackers", "exploit", "exploited", "exploits", "breach", "drained", "drainer"]},
    "audit":          {"emoji": "emoji.noto.magnifying-glass-tilted-left", "mono": "icon.icon-park-outline.file-search" , "photo": "smart contract audit", "aliases": ["audited", "audits", "security audit", "smart contract audit", "code audit"]},
    "kyc":            {"emoji": "emoji.noto.identification-card", "mono": "icon.icon-park-outline.id-card", "colour": "icon.icon-park-color.id-card", "photo": "kyc verification", "aliases": ["know your customer", "aml", "identity verification", "verification", "verified"]},
    "custody":        {"emoji": "emoji.noto.locked", "mono": "icon.carbon.bank-vault", "photo": "crypto custody", "aliases": ["custodial", "self-custody", "self custody", "non-custodial", "custodian", "custody solution"]},
    "multisig":       {"emoji": "emoji.noto.key", "photo": "multisig wallet", "aliases": ["multi-sig", "multi sig", "multisig wallet", "multi-signature", "multi signature"]},
    "satoshi":        {"emoji": "emoji.noto.bust-in-silhouette", "photo": "satoshi nakamoto", "aliases": ["sat", "sats", "satoshis", "satoshi nakamoto", "nakamoto"]},
    "halving":        {"emoji": "emoji.noto.scissors", "mono": "icon.icon-park-outline.scissors" , "photo": "bitcoin halving", "aliases": ["the halving", "halvening", "bitcoin halving", "block reward halving"]},
    "fork":           {"emoji": "emoji.noto.fork-and-knife", "mono": "icon.lucide.git-fork" , "photo": "blockchain fork", "aliases": ["forks", "hard fork", "soft fork", "hardfork", "softfork", "chain split"]},
    "genesis":        {"emoji": "emoji.noto.glowing-star", "photo": "genesis block", "aliases": ["genesis block"]},
    "mempool":        {"photo": "mempool", "aliases": ["the mempool", "memory pool"]},
    "signature":      {"emoji": "emoji.noto.writing-hand", "mono": "icon.icon-park-outline.edit-name", "photo": "digital signature", "aliases": ["signatures", "digital signature", "signing", "sign the transaction", "signed"]},
    "encryption":     {"emoji": "emoji.noto.locked-with-key", "mono": "icon.icon-park-outline.lock", "photo": "encryption", "aliases": ["encrypt", "encrypted", "end-to-end encryption", "cryptography", "cryptographic"]},
    "hash":           {"emoji": "emoji.noto.input-symbols", "mono": "icon.icon-park-outline.hashtag-key", "photo": "hash function", "aliases": ["hashing", "hashes", "hash function", "transaction hash", "txid", "hash rate"]},
    "p2p":            {"emoji": "emoji.noto.handshake", "photo": "peer to peer", "aliases": ["peer to peer", "peer-to-peer", "p2p trading", "p2p exchange"]},
    "trustless":      {"emoji": "emoji.noto.handshake", "photo": "trustless system", "aliases": ["permissionless", "trust minimized", "trustless system"]},
    "decentralized":  {"emoji": "emoji.noto.globe-with-meridians", "mono": "icon.carbon.network-3", "photo": "decentralized network", "aliases": ["decentralised", "decentralization", "decentralisation", "decentralized network", "decentralized networks"]},
    "immutable":      {"emoji": "emoji.noto.locked", "mono": "icon.icon-park-outline.lock", "photo": "immutable ledger", "aliases": ["immutability", "cannot be changed", "tamper-proof", "tamper proof"]},
    "transparent":    {"emoji": "emoji.noto.magnifying-glass-tilted-left", "photo": "transparency", "aliases": ["transparency", "open ledger", "publicly verifiable", "on-chain", "onchain"]},
    "anonymous":      {"emoji": "emoji.noto.detective", "photo": "anonymous crypto", "aliases": ["anonymity", "pseudonymous", "privacy coin", "privacy coins", "private transaction"]},
    "metaverse":      {"emoji": "emoji.noto.flying-saucer", "photo": "metaverse", "aliases": ["virtual world", "virtual worlds", "virtual land", "digital land", "metaverses"]},
    "playtoearn":     {"emoji": "emoji.noto.video-game", "photo": "play to earn", "aliases": ["play to earn", "play-to-earn", "p2e", "gamefi", "move to earn", "web3 game", "web3 games", "blockchain game", "blockchain games", "crypto game", "crypto games"]},
    "rwa":            {"emoji": "emoji.noto.building-construction", "photo": "real world assets", "aliases": ["real world assets", "real-world assets", "tokenized assets", "tokenised assets", "tokenization", "tokenisation", "tokenize", "tokenized real estate"]},
    "cbdc":           {"emoji": "emoji.noto.bank", "photo": "cbdc digital currency", "aliases": ["central bank digital currency", "digital dollar", "digital euro", "digital yuan"]},
    "fiat":           {"emoji": "emoji.noto.dollar-banknote", "mono": "icon.mingcute.currency-dollar-line", "photo": "fiat currency", "aliases": ["fiat currency", "fiat money", "traditional currency", "cash money"]},
    "onramp":         {"emoji": "emoji.noto.oncoming-automobile", "photo": "fiat onramp", "aliases": ["on-ramp", "on ramp", "off-ramp", "off ramp", "fiat onramp", "fiat on-ramp", "buy crypto with card"]},
    "regulation":     {"emoji": "emoji.noto.balance-scale", "mono": "icon.icon-park-outline.scale", "photo": "crypto regulation", "aliases": ["regulations", "regulator", "regulators", "sec", "compliance", "legal framework", "regulated"]},
    "cryptotax":      {"emoji": "emoji.noto.receipt", "photo": "crypto tax", "aliases": ["crypto tax", "crypto taxes", "tax on crypto", "tax reporting", "capital gains", "taxable event"]},
    "etf":            {"emoji": "emoji.noto.bar-chart", "colour": "icon.icon-park-color.stock-market", "mono": "icon.icon-park-outline.bill", "photo": "bitcoin etf", "aliases": ["etfs", "spot etf", "bitcoin etf", "ethereum etf", "exchange traded fund", "exchange-traded fund"]},
    "futures":        {"emoji": "emoji.noto.crystal-ball", "photo": "crypto futures", "aliases": ["perpetual", "perps", "perpetual futures", "perpetual swap", "derivatives", "crypto derivatives"]},
    "options":        {"emoji": "emoji.noto.card-file-box", "photo": "crypto options", "aliases": ["options trading", "calls and puts"]},
    "leverage":       {"emoji": "emoji.noto.high-voltage", "mono": "icon.icon-park-outline.lightning", "photo": "leverage trading", "aliases": ["leveraged", "leverage trading", "margin", "margin trading", "2x", "3x", "10x", "100x", "long position", "short position", "go long", "go short", "longing", "shorting"]},
    "liquidation":    {"emoji": "emoji.noto.chart-decreasing", "photo": "liquidation", "aliases": ["liquidated", "liquidations", "margin call", "stop loss hunt"]},
    "orderbook":      {"emoji": "emoji.noto.books", "photo": "order book", "aliases": ["order book", "order books", "depth chart", "market depth"]},
    "limitorder":     {"emoji": "emoji.noto.bullseye", "photo": "limit order", "aliases": ["limit order", "limit orders", "stop loss", "stop-loss", "take profit", "take-profit"]},
    "slippage":       {"emoji": "emoji.noto.down-arrow", "photo": "slippage", "aliases": ["price impact"]},
    "arbitrage":      {"emoji": "emoji.noto.left-right-arrow", "photo": "crypto arbitrage", "aliases": ["arb", "arbitrage trading", "price difference"]},
    "portfolio":      {"emoji": "emoji.noto.briefcase", "mono": "icon.ant-design.pie-chart-outlined", "colour": "icon.icon-park-color.finance", "photo": "crypto portfolio", "aliases": ["portfolios", "holdings", "crypto portfolio", "your bags", "bags"]},
    "trader":         {"emoji": "emoji.noto.person", "photo": "crypto trader", "aliases": ["traders", "day trader", "day trading", "swing trading", "scalping"]},
    "technicalanalysis": {"emoji": "emoji.noto.chart-increasing", "mono": "icon.tabler.chart-candle", "photo": "technical analysis", "aliases": ["technical analysis", "ta", "chart analysis", "chart patterns"]},
    "support":        {"emoji": "emoji.noto.chart-increasing", "photo": "support level", "aliases": ["support level", "resistance", "resistance level", "support and resistance", "breakout", "breakouts", "correction", "rally", "crash", "volatility", "volatile"]},
    "roi":            {"emoji": "emoji.noto.money-with-wings", "photo": "roi profit", "aliases": ["return on investment", "returns", "profit", "profits", "gains", "profitability", "making money", "earn", "earnings"]},
    "loss":           {"emoji": "emoji.noto.chart-decreasing", "photo": "trading loss", "aliases": ["losses", "losing money", "down bad"]},
    "dca":            {"emoji": "emoji.noto.calendar", "photo": "dollar cost averaging", "aliases": ["dollar cost averaging", "dollar-cost averaging", "dca strategy"]},
    "passiveincome":  {"emoji": "emoji.noto.money-bag", "photo": "passive income crypto", "aliases": ["passive income", "earn while you sleep", "income stream"]},
    "financialfreedom": {"emoji": "emoji.noto.glowing-star", "photo": "financial freedom", "aliases": ["financial freedom", "financial independence", "generational wealth", "wealth", "wealth building"]},
    "unbanked":       {"emoji": "emoji.noto.bank", "photo": "unbanked banking", "aliases": ["the unbanked", "bankless", "bank the unbanked", "financial inclusion", "banking access"]},
    "remittance":     {"emoji": "emoji.noto.globe-with-meridians", "photo": "crypto remittance", "aliases": ["remittances", "cross-border payments", "cross border payments", "international transfer", "international transfers", "send money abroad", "money transfer", "money transfers"]},
    "payment":        {"emoji": "emoji.noto.credit-card", "mono": "icon.icon-park-outline.payment-method", "colour": "icon.icon-park-color.flash-payment", "photo": "crypto payment", "aliases": ["payments", "pay with crypto", "crypto payments", "crypto payment", "pay with bitcoin", "merchant payments", "checkout"]},
    "transfer":       {"emoji": "emoji.noto.right-arrow", "photo": "crypto transfer", "aliases": ["send crypto", "receive crypto", "send", "receive", "send and receive", "sending crypto", "receiving crypto"]},
    "swap":           {"emoji": "emoji.noto.left-right-arrow", "mono": "icon.tabler.arrows-exchange", "colour": "icon.icon-park-color.exchange", "photo": "token swap", "aliases": ["swaps", "swapping", "token swap", "token swaps", "swap tokens", "swap crypto"]},
    "qrcode":         {"mono": "icon.carbon.qr-code", "emoji": "emoji.noto.input-symbols", "colour": "icon.icon-park-color.pay-code", "photo": "qr code", "aliases": ["qr code", "qr codes", "scan the qr", "scan to pay"]},
    "tvl":            {"emoji": "emoji.noto.bar-chart", "photo": "total value locked", "aliases": ["total value locked", "value locked"]},
    "impermanentloss": {"emoji": "emoji.noto.chart-decreasing", "photo": "impermanent loss", "aliases": ["impermanent loss", "il"]},
    "collateral":     {"emoji": "emoji.noto.locked", "photo": "collateral", "aliases": ["overcollateralized", "over-collateralized", "collateralized", "collateral ratio"]},
    "governance":     {"emoji": "emoji.noto.ballot-box-with-ballot", "photo": "dao governance vote", "aliases": ["governance vote", "voting", "vote", "votes", "proposal", "proposals", "governance proposal", "on-chain governance"]},
    "treasury":       {"emoji": "emoji.noto.money-bag", "photo": "dao treasury", "aliases": ["dao treasury", "protocol treasury"]},
    "community":      {"emoji": "emoji.noto.handshake", "photo": "crypto community", "aliases": ["community members", "the community", "crypto community", "ecosystem"]},
    "partnership":    {"emoji": "emoji.noto.handshake", "photo": "partnership", "aliases": ["partnerships", "partner", "collaboration", "integration", "integrations"]},
    "roadmap":        {"emoji": "emoji.noto.world-map", "photo": "project roadmap", "aliases": ["the roadmap", "project roadmap", "milestones"]},
    "launch":         {"emoji": "emoji.noto.rocket", "mono": "icon.icon-park-outline.rocket", "colour": "emoji.noto.rocket", "photo": "token launch", "aliases": ["launching", "launched", "new token", "token launch", "project launch", "goes live", "going live"]},
    "adoption":       {"emoji": "emoji.noto.chart-increasing", "photo": "crypto adoption", "aliases": ["mass adoption", "mainstream adoption", "adopt", "adopted", "crypto adoption"]},
    "utility":        {"emoji": "emoji.noto.toolbox", "photo": "token utility", "aliases": ["use case", "use cases", "real utility", "token utility"]},
    "scarcity":       {"emoji": "emoji.noto.gem-stone", "photo": "scarcity", "aliases": ["scarce", "limited supply", "fixed supply", "21 million", "digital scarcity"]},
    "supply":         {"emoji": "emoji.noto.package", "photo": "token supply", "aliases": ["circulating supply", "max supply", "total supply", "token supply", "supply cap"]},
    "burn":           {"emoji": "emoji.noto.fire", "mono": "icon.icon-park-outline.fire", "photo": "token burn", "aliases": ["burned", "burning", "token burn", "burn mechanism", "deflationary", "buy back and burn", "buyback and burn"]},
    "emission":       {"emoji": "emoji.noto.calendar", "photo": "token emissions", "aliases": ["emissions", "inflationary", "inflation rate", "emission rate"]},
    "vesting":        {"emoji": "emoji.noto.hourglass-not-done", "photo": "token vesting", "aliases": ["vest", "vested", "vesting schedule", "unlock", "unlocks", "token unlock", "token unlocks", "cliff"]},
    "zero knowledge": {"emoji": "emoji.noto.japanese-secret-button", "photo": "zero knowledge proof", "aliases": ["zero-knowledge", "zk", "zk proof", "zk proofs", "zk-snark", "zksnark", "zk-stark", "zkstark", "validity proof", "validity proofs"]},
    "mev":            {"emoji": "emoji.noto.robot", "photo": "mev bots", "aliases": ["maximal extractable value", "sandwich attack", "front running", "front-running", "mev bot"]},
    "slashing":       {"emoji": "emoji.noto.scissors", "photo": "validator slashing", "aliases": ["slashed", "slashing penalty"]},
    "finality":       {"emoji": "emoji.noto.check-mark", "photo": "transaction finality", "aliases": ["final", "confirmed", "confirmations", "block time", "instant finality"]},
    "blockexplorer":  {"emoji": "emoji.noto.magnifying-glass-tilted-left", "photo": "block explorer", "aliases": ["block explorer", "explorer", "etherscan", "bscscan", "solscan", "view on explorer"]},
    "ipfs":           {"emoji": "emoji.noto.globe-with-meridians", "photo": "ipfs storage", "aliases": ["decentralized storage", "distributed storage", "arweave", "filecoin"]},
    "ens":            {"emoji": "emoji.noto.label", "photo": "ens domain", "aliases": ["ens domain", "ens name", ".eth", "ethereum name service", "web3 domain", "web3 domains", "crypto domain"]},
    "did":            {"emoji": "emoji.noto.identification-card", "photo": "decentralized identity", "aliases": ["decentralized identity", "digital identity", "self-sovereign identity", "verifiable credentials", "soulbound", "sbt"]},
    "accountabstraction": {"emoji": "emoji.noto.gear", "photo": "account abstraction", "aliases": ["account abstraction", "smart wallet", "smart wallets", "social recovery"]},
    "seedless":       {"emoji": "emoji.noto.key", "photo": "seedless wallet", "aliases": ["seedless", "no seed phrase", "wallet recovery"]},
    "insurance":      {"emoji": "emoji.noto.umbrella", "mono": "icon.icon-park-outline.lock-one", "photo": "crypto insurance", "aliases": ["crypto insurance", "coverage", "insured", "protocol insurance"]},
    "bugbounty":      {"emoji": "emoji.noto.money-bag", "photo": "bug bounty", "aliases": ["bug bounty", "bounties", "white hat"]},
    "opensource":     {"emoji": "emoji.noto.open-book", "mono": "icon.icon-park-outline.folder-open", "colour": "icon.icon-park-color.github", "photo": "open source code", "aliases": ["open source", "open-source", "open sourced", "public code", "open code"]},
    "faucet":         {"emoji": "emoji.noto.potable-water", "photo": "testnet faucet", "aliases": ["faucets", "testnet faucet", "free test tokens"]},
    "reward":         {"emoji": "emoji.noto.trophy", "mono": "icon.lucide.award", "photo": "crypto rewards", "aliases": ["rewards", "earn rewards", "staking rewards", "block reward", "block rewards", "reward rate"]},
    "whalealert":     {"emoji": "emoji.noto.whale", "photo": "whale alert", "aliases": ["whale alert", "whale watching", "whale tracking", "smart money", "on-chain analytics", "onchain analytics"]},
    "web3":           {"colour": "brand.logos.web3js", "emoji": "emoji.noto.globe-with-meridians", "photo": "web3", "aliases": ["web 3", "web3.0", "web 3.0", "web3 ecosystem"]},
    # --- brands: exchanges / wallets / tools ---
    "coinbase":       {"colour": "brand.si.coinbase", "photo": "coinbase", "aliases": ["coinbase exchange", "coinbase wallet"]},
    "kraken":         {"colour": "brand.logos.kraken", "photo": "kraken", "aliases": ["kraken exchange"]},
    "okx":            {"colour": "brand.si.okx", "photo": "okx", "aliases": ["okx exchange"]},
    "kucoin":         {"colour": "brand.si.kucoin", "photo": "kucoin", "aliases": ["kucoin exchange"]},
    "metamask":       {"colour": "brand.logos.metamask", "emoji": "emoji.noto.fox", "photo": "metamask wallet", "aliases": ["meta mask", "metamask wallet"]},
    "phantomwallet":  {"emoji": "emoji.noto.ghost", "photo": "phantom wallet", "aliases": ["phantom", "phantom wallet"]},
    "trezorwallet":   {"colour": "brand.si.trezor", "photo": "trezor", "aliases": ["trezor", "trezor wallet"]},
    "ledgerwallet":   {"emoji": "emoji.noto.ledger", "photo": "ledger wallet", "aliases": ["ledger nano", "ledger wallet", "ledger device"]},
    "uniswap":        {"emoji": "emoji.noto.unicorn", "colour": "icon.icon-park-color.exchange", "mono": "icon.icon-park-outline.exchange", "photo": "uniswap", "aliases": ["uniswap dex"]},
    "pancakeswap":    {"emoji": "emoji.noto.pancakes", "colour": "icon.icon-park-color.cake", "photo": "pancakeswap", "aliases": ["cake token"]},
    "opensea":        {"colour": "brand.si.opensea", "photo": "opensea", "aliases": ["open sea"]},
    "rarible":        {"colour": "brand.si.rarible", "photo": "rarible", "aliases": ["rari"]},
    "coinmarketcap":  {"colour": "brand.si.coinmarketcap", "photo": "coinmarketcap", "aliases": ["coin market cap", "coinmarket cap", "cmc"]},
    "coingecko":      {"emoji": "emoji.noto.lizard", "photo": "coingecko", "aliases": ["coin gecko", "gecko terminal"]},
    "tradingview":    {"emoji": "emoji.noto.chart-increasing", "photo": "tradingview", "aliases": ["trading view", "tradingview chart"]},
    "etherscanbrand": {"emoji": "emoji.noto.magnifying-glass-tilted-left", "photo": "etherscan", "aliases": ["etherscan.io"]},
    "binancechain":   {"colour": "brand.si.bnbchain", "photo": "bnb chain", "aliases": ["bsc", "bnb smart chain", "binance smart chain", "bscscan"]},
    "ethereumchain":  {"colour": "brand.logos.ethereum", "photo": "ethereum network", "aliases": ["ethereum network", "ethereum mainnet", "eth mainnet", "evm", "evm chain", "evm chains", "ethereum virtual machine"]},
    "basechain":      {"colour": "brand.logos.base", "photo": "base chain", "aliases": ["base chain", "base network", "base blockchain", "on base", "base l2", "coinbase base"]},
    "solanachain":    {"colour": "brand.si.solana", "photo": "solana network", "aliases": ["solana network", "solana mainnet", "solana ecosystem"]},
    "wbtc":           {"photo": "wrapped bitcoin", "aliases": ["wrapped bitcoin", "wrapped btc"]},
    "dai":            {"photo": "dai stablecoin", "aliases": ["dai stablecoin", "makerdao", "maker"]},
    "lido":           {"photo": "lido staking", "aliases": ["lido finance", "steth", "staked eth"]},
    "aave":           {"emoji": "emoji.noto.ghost", "photo": "aave", "aliases": ["aave protocol"]},
    "curve":          {"photo": "curve finance", "aliases": ["crv", "curve finance"]},
    "gnosissafe":     {"emoji": "emoji.noto.locked", "photo": "safe multisig", "aliases": ["safe", "gnosis safe", "safe multisig", "safe wallet"]},
    "worldcoin":      {"emoji": "emoji.noto.globe-with-meridians", "photo": "worldcoin", "aliases": ["world coin", "wld", "world id"]},
    "hederanetwork":  {"colour": "brand.si.hedera", "photo": "hedera network", "aliases": ["hbar"]},
    "market":         {"emoji": "emoji.noto.bar-chart", "mono": "icon.icon-park-outline.shop", "colour": "icon.icon-park-color.market-analysis", "photo": "crypto market", "aliases": ["markets", "crypto market", "the market", "market conditions"]},
    "price":          {"emoji": "emoji.noto.label", "mono": "icon.ant-design.tag-outlined", "photo": "token price", "aliases": ["prices", "token price", "price of", "price target", "all-time high", "all time high", "ath", "all-time low", "all time low", "atl", "new high", "new low"]},
    "buythedip":      {"emoji": "emoji.noto.shopping-cart", "photo": "buy the dip", "aliases": ["buy the dip", "buying the dip", "accumulate", "accumulation"]},
    "greenflag":      {"emoji": "emoji.noto.check-mark-button", "photo": "green flag", "aliases": ["green flag", "green flags", "red flag", "red flags"]},
    "dyor":           {"emoji": "emoji.noto.magnifying-glass-tilted-left", "photo": "dyor research", "aliases": ["do your own research", "do your research", "not financial advice", "nfa"]},
    "shill":          {"emoji": "emoji.noto.megaphone", "photo": "shilling token", "aliases": ["shilling", "shilled", "shiller", "paid promotion", "sponsored"]},
    "bagholder":      {"emoji": "emoji.noto.shopping-bags", "photo": "bag holder", "aliases": ["bag holder", "bag holders", "bagholder", "bagholders", "left holding the bag"]},
    "gem":            {"emoji": "emoji.noto.gem-stone", "mono": "icon.lucide.gem", "colour": "icon.icon-park-color.diamond", "photo": "hidden gem", "aliases": ["gems", "hidden gem", "hidden gems", "low cap gem", "100x gem"]},
    "rocketship":     {"emoji": "emoji.noto.rocket", "mono": "icon.icon-park-outline.rocket", "colour": "icon.icon-park-color.rocket", "photo": "rocket crypto", "aliases": ["rocket", "rockets", "take off", "liftoff", "blast off"]},
    "candle":         {"emoji": "emoji.noto.candle", "mono": "icon.tabler.chart-candle", "photo": "green candle", "aliases": ["green candle", "red candle", "big green candle"]},
    "bubblechart":    {"emoji": "emoji.noto.bubbles", "photo": "bubble", "aliases": ["bubble", "bubbles", "market bubble", "speculative bubble"]},
    "onchaindata":    {"emoji": "emoji.noto.chart-increasing", "photo": "on-chain data", "aliases": ["on-chain data", "onchain data", "on-chain metrics", "blockchain data", "on-chain analysis"]},
    "smartcontractdev": {"emoji": "emoji.noto.laptop", "photo": "solidity developer", "aliases": ["solidity", "smart contract developer", "smart contract development", "web3 developer", "blockchain developer", "contract development"]},
    "gasless":        {"emoji": "emoji.noto.free-button", "photo": "gasless transactions", "aliases": ["gasless", "gas free", "zero gas", "gas-free", "no gas fees"]},
    "watchlist":      {"emoji": "emoji.noto.eyes", "photo": "watchlist", "aliases": ["watchlists", "price alert", "price alerts", "portfolio tracker", "track your crypto"]},
    "seedround":      {"emoji": "emoji.noto.chart-increasing", "photo": "crypto funding", "aliases": ["seed round", "funding round", "raised", "funding", "vc", "venture capital", "backed by"]},
    "mainstream":     {"emoji": "emoji.noto.television", "photo": "mainstream crypto", "aliases": ["mainstream", "goes mainstream", "in the news", "headlines"]},
    "deadcoin":       {"emoji": "emoji.noto.skull", "photo": "dead coin", "aliases": ["dead coin", "dead coins", "failed project", "abandoned project", "ghost chain"]},
    "sharktank":      {"emoji": "emoji.noto.shark", "photo": "crypto shark", "aliases": ["shark", "sharks", "smart investor"]},
    "influencer":     {"emoji": "emoji.noto.megaphone", "photo": "crypto influencer", "aliases": ["influencers", "crypto influencer", "crypto twitter", "ct", "kols", "kol"]},
    "telegram":       {"colour": "brand.logos.telegram", "emoji": "emoji.noto.envelope-with-arrow", "photo": "telegram", "aliases": ["telegram group", "telegram channel", "tg"]},
    "discord":        {"colour": "brand.logos.discord", "photo": "discord", "aliases": ["discord server", "discord community", "join our discord"]},
    "twitterx":       {"colour": "brand.si.x", "photo": "twitter x", "aliases": ["twitter", "x", "crypto twitter", "twitter x", "on x", "on twitter"]},
    "reddit":         {"colour": "brand.si.reddit", "photo": "reddit", "aliases": ["reddit community", "subreddit", "r/cryptocurrency"]},
    "youtube":        {"colour": "brand.logos.youtube", "photo": "youtube", "aliases": ["youtube video", "youtuber", "youtube channel"]},
    "news":           {"emoji": "emoji.noto.newspaper", "mono": "icon.ant-design.file-text-outlined", "photo": "crypto news", "aliases": ["news", "announcement", "announcements", "breaking news", "announces", "announced", "crypto news"]},
    "calendar":       {"emoji": "emoji.noto.calendar", "mono": "icon.icon-park-outline.calendar", "photo": "crypto calendar", "aliases": ["upcoming events", "important dates", "event calendar"]},
    "questionmark":   {"emoji": "emoji.noto.red-question-mark", "photo": "crypto question", "aliases": ["what is", "how does", "why does", "what are"]},
    "idea":           {"emoji": "emoji.noto.light-bulb", "mono": "icon.carbon.idea", "colour": "icon.fluent-color.lightbulb-48", "photo": "idea", "aliases": ["ideas", "innovation", "innovative", "new idea", "bright idea"]},
    "warning":        {"emoji": "emoji.noto.warning", "mono": "icon.ant-design.warning-outlined", "colour": "icon.icon-park-color.attention", "photo": "warning", "aliases": ["warn", "caution", "be careful", "watch out", "beware", "risky"]},
    "success":        {"emoji": "emoji.noto.check-mark-button", "mono": "icon.ant-design.check-circle-outlined", "colour": "icon.icon-park-color.success", "photo": "success", "aliases": ["successful", "succeeded", "win", "winning", "wins", "victory"]},
    "fail":           {"emoji": "emoji.noto.cross-mark", "mono": "icon.icon-park-outline.minus", "photo": "failure", "aliases": ["failed", "fails", "failure", "failed project", "goes wrong"]},
    "security":       {"emoji": "emoji.noto.shield", "mono": "icon.icon-park-outline.shield", "colour": "icon.icon-park-color.security", "photo": "crypto security", "aliases": ["secure", "security", "safety", "protect", "protected", "protection", "safely", "stay safe", "keep safe"]},
    "privacy":        {"emoji": "emoji.noto.locked", "mono": "icon.icon-park-outline.lock", "colour": "icon.icon-park-color.personal-privacy", "photo": "privacy", "aliases": ["private", "privacy", "confidential", "your keys your coins", "not your keys"]},
    "growth":         {"emoji": "emoji.noto.chart-increasing", "mono": "icon.icon-park-outline.chart-graph", "colour": "icon.fluent-color.data-trending-48", "photo": "growth", "aliases": ["grow", "growing", "growth", "grows", "exponential growth", "going up"]},
    "analytics":      {"emoji": "emoji.noto.bar-chart", "mono": "icon.carbon.chart-line", "photo": "crypto analytics", "aliases": ["analytics", "metrics", "statistics", "stats", "numbers", "on-chain metrics"]},
    "time":           {"emoji": "emoji.noto.alarm-clock", "mono": "icon.ant-design.clock-circle-outlined", "photo": "time", "aliases": ["timing", "early", "still early", "too late", "right time"]},
    "globe":          {"emoji": "emoji.noto.globe-showing-americas", "mono": "icon.carbon.globe", "colour": "emoji.noto.globe-with-meridians", "photo": "global", "aliases": ["global", "worldwide", "around the world", "anywhere", "borderless", "everywhere"]},
    "moneygeneric":   {"emoji": "emoji.noto.money-bag", "mono": "icon.icon-park-outline.paper-money", "colour": "icon.icon-park-color.paper-money", "photo": "money", "aliases": ["cash flow", "real money", "hard-earned money"]},
    "savings":        {"emoji": "emoji.noto.pig-face", "mono": "icon.carbon.piggy-bank", "photo": "savings", "aliases": ["save", "saving", "saved", "piggy bank", "nest egg", "your savings"]},
    "goal":           {"emoji": "emoji.noto.bullseye", "mono": "icon.carbon.chart-bar-target", "colour": "icon.icon-park-color.target", "photo": "goal", "aliases": ["goals", "target", "targets", "milestone", "objective", "objectives"]},
    "question":       {"emoji": "emoji.noto.red-question-mark", "photo": "question", "aliases": ["questions", "question"]},
    "book":           {"emoji": "emoji.noto.books", "mono": "icon.icon-park-outline.book-open", "photo": "crypto education", "aliases": ["learn", "learning", "education", "educational", "guide", "tutorial", "course", "beginner", "beginners", "explained", "explainer", "101"]},
    "video":          {"emoji": "emoji.noto.video-camera", "photo": "video", "aliases": ["videos", "watch", "watch this"]},
    "tools":          {"emoji": "emoji.noto.toolbox", "mono": "icon.ant-design.tool-outlined", "photo": "crypto tools", "aliases": ["tool", "toolkit", "tooling"]},
    "docs":           {"emoji": "emoji.noto.books", "photo": "documentation", "aliases": ["docs", "documentation", "read the docs", "guide", "guides", "tutorials"]},
    "api":            {"mono": "icon.carbon.api", "emoji": "emoji.noto.desktop-computer", "photo": "crypto api", "aliases": ["apis", "api access", "developer api", "rest api", "webhook", "webhooks"]},
    "developer":      {"emoji": "emoji.noto.laptop", "mono": "icon.icon-park-outline.code-computer", "colour": "icon.icon-park-color.code-computer", "photo": "developer", "aliases": ["developers", "dev", "devs", "dev team", "builders", "build on", "build with", "coder", "coders"]},
    "integration2":   {"emoji": "emoji.noto.puzzle-piece", "mono": "icon.icon-park-outline.puzzle", "photo": "integration", "aliases": ["integrate", "integrated", "integrates", "works with", "compatible", "plug into"]},
    "speed":          {"emoji": "emoji.noto.high-voltage", "mono": "icon.icon-park-outline.lightning", "colour": "icon.icon-park-color.speed", "photo": "fast transactions", "aliases": ["fast", "faster", "fastest", "speed", "instant", "instantly", "lightning fast", "low latency", "throughput", "tps", "transactions per second"]},
    "fees":           {"emoji": "emoji.noto.coin", "photo": "low fees", "aliases": ["fees", "low fees", "cheap", "affordable", "low cost", "low-cost", "near zero fees", "fractions of a penny"]},
    "scale":          {"emoji": "emoji.noto.bar-chart", "photo": "scaling", "aliases": ["scaling", "scalable", "scalability", "scale", "scales", "massively scalable"]},
    "audittrail":     {"emoji": "emoji.noto.magnifying-glass-tilted-left", "photo": "audit trail", "aliases": ["audit trail", "trackable", "traceable", "verifiable", "provable", "prove"]},
    "permanent":      {"emoji": "emoji.noto.locked", "photo": "permanent record", "aliases": ["permanent", "permanently", "forever", "immutable record", "cannot be deleted", "uncensorable", "censorship resistant", "censorship resistance"]},
    "middleman":      {"emoji": "emoji.noto.no-entry", "photo": "no middleman", "aliases": ["middleman", "middlemen", "no middleman", "cut out the middleman", "intermediary", "intermediaries", "third party", "third parties", "counterparty", "counterparty risk"]},
    "ownership":      {"emoji": "emoji.noto.key", "photo": "true ownership", "aliases": ["own", "ownership", "you own", "true ownership", "your keys", "own your", "digital ownership", "self-sovereign"]},
    "borderless":     {"emoji": "emoji.noto.globe-with-meridians", "photo": "borderless money", "aliases": ["borderless", "no borders", "without borders", "global payments", "anyone anywhere"]},
    "peertopeer":     {"emoji": "emoji.noto.handshake", "photo": "peer to peer", "aliases": ["person to person", "direct transfer", "wallet to wallet"]},
    "clock247":       {"emoji": "emoji.noto.alarm-clock", "photo": "24/7 markets", "aliases": ["24/7", "24 7", "24-7", "always on", "never closes", "never sleeps", "anytime"]},
    "banking":        {"emoji": "emoji.noto.bank", "mono": "icon.icon-park-outline.bank", "photo": "banking", "aliases": ["bank", "banks", "bank account", "bank accounts", "banking system", "traditional finance", "tradfi", "wire transfer", "wire transfers"]},
    "government":     {"emoji": "emoji.noto.bank", "photo": "government", "aliases": ["governments", "regulators", "policy", "policies", "law", "laws", "legislation"]},
    "creditcard":     {"emoji": "emoji.noto.credit-card", "mono": "icon.icon-park-outline.bank-card", "colour": "icon.icon-park-color.bank-card", "photo": "credit card", "aliases": ["credit card", "credit cards", "debit card", "debit cards", "card payment", "card payments", "visa", "mastercard"]},
    "percent":        {"emoji": "emoji.noto.japanese-discount-button", "mono": "icon.icon-park-outline.percentage", "colour": "icon.icon-park-color.percentage", "photo": "percent", "aliases": ["percent", "percentage", "%", "apy", "apr", "interest rate", "interest rates", "rate", "rates"]},
    "cashback":       {"emoji": "emoji.noto.money-with-wings", "photo": "cashback", "aliases": ["cash back", "cash-back", "rewards program", "earn crypto back"]},
    "subscription":   {"emoji": "emoji.noto.calendar", "photo": "subscription", "aliases": ["subscriptions", "subscribe", "monthly", "recurring", "premium", "plan", "plans", "tier", "tiers"]},
    "walletconnect":  {"emoji": "emoji.noto.link", "photo": "wallet connect", "aliases": ["walletconnect", "connect wallet", "connect your wallet", "wallet connection"]},
    "delegation":     {"emoji": "emoji.noto.handshake", "photo": "delegation", "aliases": ["delegate", "delegating", "delegated", "delegator", "delegators", "delegate stake"]},
    "epoch":          {"emoji": "emoji.noto.calendar", "photo": "epoch", "aliases": ["epochs", "era", "eras"]},
    "nodeoperator":   {"emoji": "emoji.noto.desktop-computer", "photo": "node operator", "aliases": ["node operator", "run a node", "running a node", "node runner"]},
    "airgap":         {"emoji": "emoji.noto.locked", "photo": "air gapped", "aliases": ["air-gapped", "air gapped", "airgap", "offline signing", "offline storage"]},
    "passkey":        {"emoji": "emoji.noto.key", "photo": "passkey", "aliases": ["passkeys", "pass key", "passphrase", "pass phrase"]},
    "socialfi":       {"emoji": "emoji.noto.speech-balloon", "photo": "socialfi", "aliases": ["social fi", "web3 social", "decentralized social", "deso"]},
    "depin":          {"emoji": "emoji.noto.globe-with-meridians", "photo": "depin network", "aliases": ["depin", "physical infrastructure", "decentralized infrastructure"]},
    "ordinals":       {"photo": "bitcoin ordinals", "aliases": ["ordinal", "inscriptions", "inscription", "bitcoin nft", "bitcoin nfts", "brc20", "brc-20"]},
    "runes":          {"photo": "bitcoin runes", "aliases": ["rune", "runes protocol"]},
    "erc20":          {"photo": "erc-20 token", "aliases": ["erc-20", "erc20 token", "erc-721", "erc721", "erc-1155", "token standard", "token standards"]},
    "liquidtoken":    {"emoji": "emoji.noto.droplet", "photo": "liquid token", "aliases": ["liquid staking token", "lst", "lsts", "lrt", "lrts", "liquid restaking"]},
    "restaking":      {"emoji": "emoji.noto.repeat-button", "photo": "restaking", "aliases": ["restake", "restaked", "eigenlayer", "eigen layer"]},
    "modular":        {"emoji": "emoji.noto.puzzle-piece", "photo": "modular blockchain", "aliases": ["modular blockchain", "modular blockchains", "modularity"]},
    "dataavailability": {"photo": "data availability", "aliases": ["data availability", "da layer", "celestia", "eigenda"]},
    "sequencer":      {"photo": "sequencer", "aliases": ["sequencers", "prover", "provers"]},
    "onchain":        {"emoji": "emoji.noto.link", "photo": "on chain", "aliases": ["on chain", "on-chain", "onchain", "fully on-chain", "off-chain", "offchain", "off chain"]},
    "gasfee2":        {"emoji": "emoji.noto.coin", "photo": "gas fees", "aliases": ["high fees", "expensive fees", "fee"]},
    "whitelist":      {"emoji": "emoji.noto.check-box-with-check", "photo": "whitelist", "aliases": ["whitelisted", "allowlist", "allow-listed", "early access", "waitlist", "waitlisted"]},
    "snapshot":       {"emoji": "emoji.noto.camera", "photo": "snapshot vote", "aliases": ["snapshot vote", "snapshot voting", "governance snapshot"]},
    "multichain":     {"emoji": "emoji.noto.chains", "photo": "multichain", "aliases": ["multi-chain", "multi chain", "omnichain", "cross-chain", "crosschain", "interoperability", "interoperable", "interop"]},
    "cosmosnetwork":  {"photo": "cosmos network", "aliases": ["ibc", "inter-blockchain", "cosmos sdk", "tendermint"]},
    "clawback":       {"emoji": "emoji.noto.left-arrow", "photo": "clawback", "aliases": ["claw back", "reverse transaction", "reversible"]},
    "insurtech":      {"emoji": "emoji.noto.umbrella", "photo": "insurance", "aliases": ["insurtech"]},
    "atomic":         {"emoji": "emoji.noto.atom-symbol", "photo": "atomic swap", "aliases": ["atomic swap", "atomic swaps", "atomic settlement"]},
    "settlement":     {"emoji": "emoji.noto.check-mark", "photo": "settlement", "aliases": ["settle", "settled", "settles", "settlement layer", "final settlement", "instant settlement"]},
    "provenance":     {"emoji": "emoji.noto.scroll", "photo": "provenance", "aliases": ["provable history", "track record", "verifiable history", "supply chain tracking", "supply chain"]},
    "digitalidentity2": {"emoji": "emoji.noto.identification-card", "photo": "digital identity", "aliases": ["identity", "identities", "id", "your identity", "online identity"]},
    "prediction":     {"emoji": "emoji.noto.crystal-ball", "photo": "prediction market", "aliases": ["prediction market", "prediction markets", "betting", "polymarket", "forecast"]},
    "lottery":        {"emoji": "emoji.noto.slot-machine", "photo": "crypto lottery", "aliases": ["lottery", "raffle", "prize pool"]},
    "gameasset":      {"emoji": "emoji.noto.video-game", "photo": "game assets", "aliases": ["in-game items", "game items", "skins", "game assets", "virtual items", "in-game assets", "in game items"]},
    "creator":        {"emoji": "emoji.noto.artist-palette", "photo": "content creator", "aliases": ["creators", "content creator", "content creators", "artist", "artists", "creator economy", "fan token", "fan tokens", "social token", "creator coin"]},
    "musician":       {"emoji": "emoji.noto.musical-note", "photo": "music nft", "aliases": ["music nft", "music nfts", "musician", "musicians", "royalties", "royalty"]},
    "realestate":     {"emoji": "emoji.noto.building-construction", "photo": "real estate", "aliases": ["real estate", "property", "properties", "tokenized real estate", "fractional ownership", "real world asset"]},
    "goldtoken":      {"emoji": "emoji.noto.crown", "photo": "gold backed token", "aliases": ["gold-backed", "gold backed", "gold token", "paxg", "gold-backed token", "commodity", "commodities", "precious metals"]},
    "stocks":         {"emoji": "emoji.noto.chart-increasing", "photo": "tokenized stocks", "aliases": ["stock", "stocks", "equities", "tokenized stocks", "stock market", "shares", "share"]},
    "tradfi":         {"emoji": "emoji.noto.bank", "photo": "traditional finance", "aliases": ["traditional finance", "wall street", "institutions", "institutional", "institutional investors", "hedge fund", "hedge funds", "blackrock", "fidelity"]},
    "bankless2":      {"emoji": "emoji.noto.globe-with-meridians", "photo": "bankless", "aliases": ["self-sovereign money", "your own bank", "be your own bank"]},
}

AI = {
    # --- brands ---
    "openai":         {"colour": "brand.logos.openai", "photo": "openai", "aliases": ["chatgpt", "chat gpt", "gpt", "gpt-4", "gpt-5", "gpt4", "gpt5", "gpt-4o", "dall-e", "dalle", "sora", "chatgpt plus", "open ai"]},
    "anthropic":      {"colour": "brand.logos.anthropic", "photo": "anthropic", "aliases": []},
    "claude":         {"colour": "brand.logos.claude", "photo": "claude ai", "aliases": ["claude code", "claude sonnet", "claude opus"]},
    "gemini":         {"colour": "brand.logos.google-gemini", "photo": "google gemini", "aliases": ["google gemini", "bard", "google bard", "gemini pro", "gemini flash", "google ai", "deepmind", "google deepmind"]},
    "mistral":        {"colour": "brand.logos.mistral-ai", "photo": "mistral ai", "aliases": ["mistral ai", "mistralai", "mixtral", "le chat"]},
    "deepseek":       {"colour": "brand.logos.deepseek", "photo": "deepseek", "aliases": ["deep seek", "deepseek r1", "deepseek v3"]},
    "grok":           {"colour": "brand.logos.grok", "photo": "grok", "aliases": ["xai", "x.ai", "grok ai"]},
    "perplexity":     {"colour": "brand.logos.perplexity", "photo": "perplexity", "aliases": ["perplexity ai"]},
    "huggingface":    {"colour": "brand.logos.hugging-face", "emoji": "emoji.noto.hugging-face", "photo": "hugging face", "aliases": ["hugging face", "hf", "huggingface hub", "hf hub"]},
    "ollama":         {"colour": "brand.si.ollama", "photo": "ollama", "aliases": ["ollama local", "lm studio", "lmstudio"]},
    "midjourney":     {"colour": "brand.logos.midjourney", "photo": "midjourney", "aliases": ["mid journey"]},
    "stabilityai":    {"colour": "brand.logos.stability-ai", "photo": "stability ai", "aliases": ["stability ai", "stable diffusion", "sdxl", "stable diffusion xl", "stability"]},
    "elevenlabs":     {"colour": "brand.logos.elevenlabs", "photo": "elevenlabs", "aliases": ["11labs", "eleven labs", "elevenlabs voice"]},
    "suno":           {"colour": "brand.si.suno", "photo": "suno ai", "aliases": ["suno ai", "suno music"]},
    "nvidia":         {"colour": "brand.logos.nvidia", "photo": "nvidia gpu", "aliases": ["nvidia gpu", "nvda", "geforce", "nvidia chips", "nvidia gpus"]},
    "amd":            {"colour": "brand.logos.amd", "photo": "amd gpu", "aliases": ["amd gpu", "radeon"]},
    "intel":          {"colour": "brand.logos.intel", "photo": "intel", "aliases": ["intel chip", "intel chips"]},
    "qualcomm":       {"colour": "brand.logos.qualcomm", "photo": "qualcomm", "aliases": ["snapdragon"]},
    "githubcopilot":  {"colour": "brand.logos.github-copilot", "photo": "github copilot", "aliases": ["github copilot", "copilot", "copilot x"]},
    "cursor":         {"colour": "brand.logos.cursor", "photo": "cursor ai", "aliases": ["cursor ai", "cursor editor", "cursor ide"]},
    "windsurf":       {"colour": "brand.si.windsurf", "photo": "windsurf", "aliases": ["codeium"]},
    "replit":         {"colour": "brand.logos.replit", "photo": "replit", "aliases": ["replit agent"]},
    "lovable":        {"colour": "brand.logos.lovable", "photo": "lovable", "aliases": ["lovable ai"]},
    "vercel":         {"colour": "brand.logos.vercel", "photo": "vercel", "aliases": ["v0", "vercel ai", "ai sdk"]},
    "zapier":         {"colour": "brand.logos.zapier", "photo": "zapier", "aliases": ["zapier automation", "zap"]},
    "n8n":            {"colour": "brand.logos.n8n", "photo": "n8n", "aliases": ["n8n workflow"]},
    "notion":         {"colour": "brand.logos.notion", "photo": "notion ai", "aliases": ["notion ai"]},
    "figma":          {"colour": "brand.logos.figma", "photo": "figma", "aliases": ["figma ai", "figma make"]},
    "grammarly":      {"colour": "brand.logos.grammarly", "photo": "grammarly", "aliases": []},
    "deepl":          {"colour": "brand.si.deepl", "photo": "deepl", "aliases": ["deep l"]},
    "descript":       {"colour": "brand.logos.descript", "photo": "descript", "aliases": []},
    "tensorflow":     {"colour": "brand.logos.tensorflow", "photo": "tensorflow", "aliases": ["tf", "tensor flow"]},
    "pytorch":        {"colour": "brand.logos.pytorch", "photo": "pytorch", "aliases": ["py torch", "torch"]},
    "keras":          {"colour": "brand.si.keras", "photo": "keras", "aliases": []},
    "scikitlearn":    {"colour": "brand.si.scikitlearn", "photo": "scikit learn", "aliases": ["scikit-learn", "scikit learn", "sklearn"]},
    "onnx":           {"colour": "brand.si.onnx", "photo": "onnx", "aliases": ["onnx runtime"]},
    "opencv":         {"colour": "brand.logos.opencv", "photo": "opencv", "aliases": ["open cv"]},
    "langchain":      {"colour": "brand.si.langchain", "photo": "langchain", "aliases": ["lang chain", "langgraph"]},
    "llamaindex":     {"emoji": "emoji.noto.books", "photo": "llamaindex", "aliases": ["llama index", "llama-index"]},
    "haystack":       {"colour": "brand.si.haystack", "photo": "haystack ai", "aliases": []},
    "vllm":           {"colour": "brand.si.vllm", "photo": "vllm", "aliases": ["vllm serving"]},
    "pinecone":       {"colour": "brand.logos.pinecone", "photo": "pinecone", "aliases": ["pinecone db"]},
    "qdrant":         {"colour": "brand.logos.qdrant", "photo": "qdrant", "aliases": []},
    "milvus":         {"colour": "brand.logos.milvus", "photo": "milvus", "aliases": []},
    "chroma":         {"colour": "brand.logos.chroma", "photo": "chroma db", "aliases": ["chroma db", "chromadb"]},
    "crewai":         {"colour": "brand.si.crewai", "photo": "crewai", "aliases": ["crew ai"]},
    "dify":           {"colour": "brand.si.dify", "photo": "dify", "aliases": ["dify ai"]},
    "gradio":         {"colour": "brand.logos.gradio", "photo": "gradio", "aliases": ["gradio app"]},
    "streamlit":      {"colour": "brand.logos.streamlit", "photo": "streamlit", "aliases": []},
    "replicate":      {"colour": "brand.si.replicate", "photo": "replicate", "aliases": []},
    "openrouter":     {"colour": "brand.si.openrouter", "photo": "openrouter", "aliases": ["open router"]},
    "kaggle":         {"colour": "brand.si.kaggle", "photo": "kaggle", "aliases": ["kaggle competition"]},
    "jupyter":        {"colour": "brand.logos.jupyter", "photo": "jupyter", "aliases": ["jupyter notebook", "notebook"]},
    "mcp":            {"colour": "brand.si.modelcontextprotocol", "photo": "model context protocol", "aliases": ["model context protocol", "mcp server", "mcp servers", "mcp tool"]},
    "metaai":         {"colour": "brand.si.metaai", "photo": "meta ai", "aliases": ["meta ai", "llama", "llama 3", "llama 4", "llama model", "meta llama"]},
    "moonshot":       {"colour": "brand.logos.moonshot-ai", "photo": "moonshot ai", "aliases": ["moonshot ai", "kimi", "kimi ai"]},
    "supabase":       {"colour": "brand.logos.supabase", "photo": "supabase", "aliases": ["supabase vector"]},
    "firebase":       {"colour": "brand.logos.firebase", "photo": "firebase", "aliases": ["firebase ai"]},
    "docker":         {"colour": "brand.logos.docker", "photo": "docker", "aliases": ["container", "containers", "containerized"]},
    "kubernetes":     {"colour": "brand.logos.kubernetes", "photo": "kubernetes", "aliases": ["k8s", "kubernetes cluster"]},
    "github":         {"colour": "brand.logos.github", "photo": "github", "aliases": ["git hub", "repo", "repository", "github repo"]},
    "python":         {"colour": "brand.logos.python", "photo": "python", "aliases": ["python code", "python script", "py"]},
    "appleinc":       {"colour": "brand.logos.apple", "photo": "apple inc", "aliases": ["apple inc", "apple stock", "aapl", "apple company", "apple intelligence", "apple silicon", "iphone", "ipad", "macbook", "ios", "apple watch", "apple tv", "apple m1", "apple m2", "apple m3", "apple m4", "apple vision pro"]},
    "googlegeneric":  {"colour": "brand.logos.google", "photo": "google", "aliases": ["google", "google search", "gmail", "workspace", "google workspace"]},
    "microsoft":      {"colour": "brand.logos.microsoft", "photo": "microsoft", "aliases": ["microsoft copilot", "windows", "azure", "office", "microsoft 365", "copilot 365"]},
    "metageneric":    {"colour": "brand.logos.meta", "photo": "meta", "aliases": ["meta", "facebook", "instagram", "whatsapp", "threads", "mark zuckerberg", "zuckerberg"]},
    "amazon":         {"photo": "amazon aws", "aliases": ["amazon", "aws", "amazon web services", "aws bedrock", "bedrock", "sagemaker"]},
    "stripe":         {"colour": "brand.logos.stripe", "photo": "stripe", "aliases": ["stripe payments"]},
    "slack":          {"colour": "brand.logos.slack", "photo": "slack", "aliases": ["slack bot"]},
    "spotify":        {"colour": "brand.logos.spotify", "photo": "spotify", "aliases": []},
    "tiktok":         {"colour": "brand.logos.tiktok", "photo": "tiktok", "aliases": ["tik tok"]},
    # --- core AI concepts ---
    "ai":             {"mono": "icon.icon-park-outline.brain", "emoji": "emoji.noto.robot", "colour": "icon.icon-park-color.robot", "photo": "artificial intelligence", "aliases": ["artificial intelligence", "a.i.", "ai's", "the ai", "an ai"]},
    "machinelearning": {"mono": "icon.icon-park-outline.brain", "emoji": "emoji.noto.brain", "photo": "machine learning", "aliases": ["machine learning", "ml", "ml model", "ml models"]},
    "deeplearning":   {"mono": "icon.carbon.network-4", "emoji": "emoji.noto.brain", "photo": "deep learning", "aliases": ["deep learning", "deep neural", "deep neural network"]},
    "neuralnetwork":  {"mono": "icon.carbon.network-4", "emoji": "emoji.noto.brain", "colour": "icon.icon-park-color.neural", "photo": "neural network", "aliases": ["neural network", "neural networks", "neural net", "neural nets", "ann", "artificial neural network"]},
    "transformer":    {"mono": "icon.carbon.network-4", "emoji": "emoji.noto.brain", "photo": "transformer model", "aliases": ["transformer", "transformers", "transformer model", "transformer architecture", "attention mechanism", "self attention", "self-attention"]},
    "llm":            {"mono": "icon.icon-park-outline.brain", "emoji": "emoji.noto.speech-balloon", "colour": "icon.icon-park-color.neural", "photo": "large language model", "aliases": ["llm", "llms", "large language model", "large language models", "language model", "language models", "foundation model", "foundation models", "frontier model", "frontier models"]},
    "generativeai":   {"emoji": "emoji.noto.sparkles", "mono": "icon.icon-park-outline.magic", "colour": "icon.icon-park-color.magic", "photo": "generative ai", "aliases": ["generative ai", "genai", "gen ai", "generative model", "generative models", "ai generated", "ai-generated", "generated by ai"]},
    "diffusion":      {"emoji": "emoji.noto.artist-palette", "photo": "diffusion model", "aliases": ["diffusion model", "diffusion models", "image diffusion", "latent diffusion"]},
    "prompt":         {"mono": "icon.icon-park-outline.edit-name", "emoji": "emoji.noto.memo", "colour": "icon.icon-park-color.code-computer", "photo": "ai prompt", "aliases": ["prompts", "prompting", "prompt engineering", "prompt engineer", "write a prompt", "system prompt", "good prompt"]},
    "contextwindow":  {"emoji": "emoji.noto.window", "photo": "context window", "aliases": ["context window", "context length", "context", "tokens of context", "token limit", "context size"]},
    "aitoken":        {"emoji": "emoji.noto.input-symbols", "photo": "llm tokens", "aliases": ["tokens", "tokenizer", "tokenization", "token count", "per token", "tokens per second", "million tokens"]},
    "embedding":      {"mono": "icon.carbon.chart-line-data", "emoji": "emoji.noto.dizzy", "photo": "vector embeddings", "aliases": ["embedding", "embeddings", "vector", "vectors", "vector embedding", "vector embeddings"]},
    "vectordb":       {"mono": "icon.ant-design.database-outlined", "emoji": "emoji.noto.card-file-box", "colour": "icon.icon-park-color.database-code", "photo": "vector database", "aliases": ["vector database", "vector db", "vector store", "vector search", "semantic search", "similarity search", "nearest neighbor"]},
    "rag":            {"emoji": "emoji.noto.books", "photo": "retrieval augmented generation", "aliases": ["rag", "retrieval augmented", "retrieval-augmented", "retrieval augmented generation", "grounded generation", "retrieve", "retrieval"]},
    "finetuning":     {"emoji": "emoji.noto.control-knobs", "mono": "icon.carbon.settings-adjust", "photo": "fine tuning", "aliases": ["fine-tuning", "fine tuning", "fine-tune", "finetune", "fine-tuned", "fine tuned", "finetuning", "custom model", "train your own"]},
    "training":       {"emoji": "emoji.noto.hammer-and-wrench", "photo": "model training", "aliases": ["training", "train", "trained", "trains", "model training", "training run", "pretraining", "pre-training", "pretrained", "pre-trained", "post-training", "post training", "training data", "training dataset"]},
    "inference":      {"emoji": "emoji.noto.fast-forward-button", "photo": "model inference", "aliases": ["inferencing", "inference cost", "inference time", "serving", "model serving", "deploy", "deployed", "deployment", "in production", "production"]},
    "agent":          {"mono": "icon.icon-park-outline.robot", "emoji": "emoji.noto.robot", "colour": "icon.icon-park-color.robot", "photo": "ai agent", "aliases": ["agents", "ai agent", "ai agents", "agentic", "agentic ai", "autonomous agent", "autonomous agents", "multi-agent", "multiagent", "agent workflow", "agent workflows"]},
    "tooluse":        {"emoji": "emoji.noto.toolbox", "photo": "ai tool use", "aliases": ["tool use", "tool calling", "function calling", "use tools", "tools", "ai tools"]},
    "automation":     {"mono": "icon.icon-park-outline.robot", "emoji": "emoji.noto.gear", "colour": "icon.icon-park-color.robot-one", "photo": "ai automation", "aliases": ["automate", "automated", "automates", "automating", "workflow", "workflows", "automated workflow", "auto-pilot", "autopilot", "hands-free", "set it and forget it"]},
    "chatbot":        {"emoji": "emoji.noto.speech-balloon", "mono": "icon.icon-park-outline.message", "colour": "icon.fluent-color.chat-48", "photo": "ai chatbot", "aliases": ["chatbots", "chat bot", "ai chat", "chat with ai", "talk to ai", "conversational ai", "chat interface", "ai conversation"]},
    "assistant":      {"emoji": "emoji.noto.speech-balloon", "photo": "ai assistant", "aliases": ["assistants", "ai assistant", "personal assistant", "virtual assistant", "ai helper", "sidekick", "copilots"]},
    "copilotconcept": {"emoji": "emoji.noto.airplane", "photo": "ai copilot", "aliases": ["co-pilot", "ai copilot"]},
    "avatar":         {"emoji": "emoji.noto.bust-in-silhouette", "photo": "ai avatar", "aliases": ["avatars", "ai avatar", "ai avatars", "digital human", "digital humans", "ai presenter", "virtual presenter", "talking head", "talking avatar", "presenter"]},
    "voiceclone":     {"emoji": "emoji.noto.microphone", "mono": "icon.ri.chat-voice-line", "colour": "icon.icon-park-color.voice", "photo": "voice cloning", "aliases": ["voice clone", "voice cloning", "cloned voice", "clone your voice", "cloning", "voice replica", "synthetic voice", "ai voice", "ai voices"]},
    "tts":            {"emoji": "emoji.noto.speaker-high-volume", "photo": "text to speech", "aliases": ["text to speech", "text-to-speech", "tts", "voiceover", "voice over", "narration", "read aloud", "voice synthesis", "speech synthesis"]},
    "stt":            {"emoji": "emoji.noto.microphone", "photo": "speech to text", "aliases": ["speech to text", "speech-to-text", "stt", "transcription", "transcribe", "transcribed", "transcripts", "speech recognition", "voice recognition", "whisper"]},
    "nlp":            {"emoji": "emoji.noto.books", "photo": "natural language processing", "aliases": ["nlp", "natural language processing", "natural language understanding", "nlu", "language understanding", "natural language"]},
    "computervision": {"emoji": "emoji.noto.eye", "mono": "icon.lucide.eye", "colour": "icon.icon-park-color.eyes", "photo": "computer vision", "aliases": ["computer vision", "cv", "image recognition", "object detection", "vision model", "vision models", "sees images", "image understanding"]},
    "ocr":            {"emoji": "emoji.noto.page-facing-up", "photo": "ocr text extraction", "aliases": ["ocr", "optical character recognition", "text extraction", "read text", "extract text", "document parsing", "parse documents", "read documents"]},
    "facerecognition": {"emoji": "emoji.noto.eye", "photo": "face recognition", "aliases": ["face recognition", "facial recognition", "face id", "face detection", "faces"]},
    "imagegen":       {"emoji": "emoji.noto.framed-picture", "mono": "icon.icon-park-outline.picture-album", "colour": "icon.icon-park-color.picture", "photo": "ai image generation", "aliases": ["image generation", "text to image", "text-to-image", "ai image", "ai images", "ai art", "ai artwork", "generate images", "generated image", "image to image", "ai pictures", "ai picture"]},
    "videogen":       {"emoji": "emoji.noto.movie-camera", "mono": "icon.ant-design.video-camera-outlined", "colour": "icon.icon-park-color.video", "photo": "ai video generation", "aliases": ["video generation", "text to video", "text-to-video", "ai video", "ai videos", "generate video", "generated video", "ai film", "ai movie", "image to video"]},
    "audiogen":       {"emoji": "emoji.noto.musical-note", "photo": "ai music generation", "aliases": ["music generation", "ai music", "generated music", "ai song", "ai songs", "audio generation", "sound effects", "ai audio"]},
    "codegen":        {"emoji": "emoji.noto.laptop", "mono": "icon.icon-park-outline.code", "colour": "icon.icon-park-color.code", "photo": "ai code generation", "aliases": ["code generation", "ai code", "writes code", "write code", "coding assistant", "pair programmer", "ai programming", "vibe coding", "vibe code", "generates code", "generated code"]},
    "hallucination":  {"emoji": "emoji.noto.face-in-clouds", "photo": "ai hallucination", "aliases": ["hallucinate", "hallucinates", "hallucinated", "makes things up", "made up", "confabulation", "wrong answers", "inaccurate"]},
    "bias":           {"emoji": "emoji.noto.balance-scale", "photo": "ai bias", "aliases": ["biased", "ai bias", "model bias", "fairness", "unfair", "discrimination"]},
    "alignment":      {"emoji": "emoji.noto.bullseye", "photo": "ai alignment", "aliases": ["aligned", "ai alignment", "aligned with", "aligns with human"]},
    "aisafety":       {"emoji": "emoji.noto.shield", "mono": "icon.icon-park-outline.shield", "colour": "icon.icon-park-color.security", "photo": "ai safety", "aliases": ["ai safety", "safe ai", "safety", "guardrails", "guard rails", "responsible ai", "ai risk", "ai risks"]},
    "explainable":    {"emoji": "emoji.noto.magnifying-glass-tilted-left", "photo": "explainable ai", "aliases": ["explainability", "explainable ai", "xai explainability", "interpretability", "interpretable", "black box", "transparent model"]},
    "evaluation":     {"emoji": "emoji.noto.clipboard", "photo": "model evaluation", "aliases": ["eval", "evals", "evaluate", "evaluating", "benchmark", "benchmarks", "benchmarked", "leaderboard", "tested", "accuracy", "accurate"]},
    "dataset":        {"emoji": "emoji.noto.card-index", "mono": "icon.ant-design.database-outlined", "colour": "icon.icon-park-color.database-code", "photo": "training dataset", "aliases": ["datasets", "data set", "data sets", "training set", "test set", "labeled data", "labelled data", "data labeling", "annotation", "annotated"]},
    "parameters":     {"emoji": "emoji.noto.control-knobs", "photo": "model parameters", "aliases": ["parameter", "parameters", "weights", "model weights", "billion parameters", "7b", "70b", "405b", "model size"]},
    "quantization":   {"emoji": "emoji.noto.scissors", "photo": "model quantization", "aliases": ["quantize", "quantized", "quantisation", "quantization", "4-bit", "8-bit", "gguf", "compressed model", "smaller model"]},
    "distillation":   {"emoji": "emoji.noto.test-tube", "photo": "model distillation", "aliases": ["distill", "distilled", "distilled model", "model distillation", "student model", "teacher model"]},
    "opensourceai":   {"emoji": "emoji.noto.open-book", "mono": "icon.icon-park-outline.folder-open", "colour": "icon.icon-park-color.github", "photo": "open source ai", "aliases": ["open source", "open-source", "open weights", "open weight", "open model", "open models", "open source model", "open source models", "open-source ai", "openai-compatible"]},
    "gpu":            {"mono": "icon.icon-park-outline.cpu", "emoji": "emoji.noto.desktop-computer", "colour": "icon.icon-park-color.cpu", "photo": "gpu", "aliases": ["gpus", "graphics card", "graphics cards", "tpu", "accelerator", "accelerators", "compute", "compute power", "flops", "cuda", "inference chips", "ai chips", "ai chip", "chips", "datacenter gpu", "h100", "b200", "gpu cluster"]},
    "edge":           {"emoji": "emoji.noto.mobile-phone", "photo": "edge ai", "aliases": ["edge ai", "on-device", "on device", "on device ai", "local ai", "runs locally", "runs on device", "offline ai", "no cloud"]},
    "cloudai":        {"emoji": "emoji.noto.cloud", "mono": "icon.icon-park-outline.cloud-storage", "colour": "icon.fluent-color.cloud-48", "photo": "cloud ai", "aliases": ["cloud ai", "in the cloud", "cloud-based", "cloud hosted", "hosted model", "cloud gpu", "cloud compute"]},
    "agi":            {"emoji": "emoji.noto.brain", "photo": "artificial general intelligence", "aliases": ["agi", "artificial general intelligence", "general intelligence", "human-level ai", "human level ai"]},
    "singularity":    {"emoji": "emoji.noto.cyclone", "photo": "ai singularity", "aliases": ["the singularity", "superintelligence", "asi", "super intelligence"]},
    "regulation_ai":  {"emoji": "emoji.noto.balance-scale", "photo": "ai regulation", "aliases": ["ai regulation", "ai regulations", "ai law", "ai laws", "eu ai act", "ai act", "ai policy", "ai governance", "regulate ai", "regulated ai"]},
    "copyright":      {"emoji": "emoji.noto.page-facing-up", "photo": "ai copyright", "aliases": ["copyright", "copyrighted", "fair use", "training data rights", "licensed data", "ip", "intellectual property"]},
    "watermark":      {"emoji": "emoji.noto.label", "photo": "ai watermark", "aliases": ["watermark", "watermarked", "watermarking", "provenance", "c2pa", "content credentials", "ai detection", "detect ai"]},
    "syntheticdata":  {"emoji": "emoji.noto.test-tube", "photo": "synthetic data", "aliases": ["synthetic data", "synthetic datasets", "generated data", "artificial data"]},
    "humanintheloop": {"emoji": "emoji.noto.person", "photo": "human in the loop", "aliases": ["human in the loop", "hitl", "human oversight", "human review", "human approval", "keeps a human", "humans stay", "human control"]},
    "robot":          {"mono": "icon.icon-park-outline.robot", "emoji": "emoji.noto.robot", "colour": "icon.icon-park-color.robot", "photo": "robot", "aliases": ["robots", "robotics", "humanoid", "humanoid robot", "humanoid robots", "robot arm", "warehouse robot"]},
    "selfdriving":    {"emoji": "emoji.noto.automobile", "photo": "self driving car", "aliases": ["self-driving", "self driving", "autonomous vehicle", "autonomous vehicles", "autonomous car", "driverless", "full self-driving", "fsd", "robotaxi", "autopilot"]},
    "drone":          {"emoji": "emoji.noto.flying-saucer", "photo": "drone", "aliases": ["drones", "ai drone", "delivery drone", "surveillance drone"]},
    "recommendation": {"emoji": "emoji.noto.bullseye", "photo": "recommendation engine", "aliases": ["recommendations", "recommends", "recommended", "recommendation engine", "for you page", "algorithmic feed", "the algorithm"]},
    "personalization": {"emoji": "emoji.noto.sparkle", "photo": "personalization", "aliases": ["personalized", "personalised", "personalized ai", "custom ai", "tailored", "tailored to you", "learns your", "learns you"]},
    "search_ai":      {"emoji": "emoji.noto.right-pointing-magnifying-glass", "mono": "icon.icon-park-outline.search", "photo": "ai search", "aliases": ["ai search", "search engine", "answer engine", "ai answers", "deep research", "ai-powered search"]},
    "translation":    {"emoji": "emoji.noto.globe-with-meridians", "photo": "ai translation", "aliases": ["translate", "translated", "translates", "translation", "machine translation", "any language", "languages", "multilingual", "real-time translation"]},
    "summarization":  {"emoji": "emoji.noto.page-facing-up", "photo": "ai summarization", "aliases": ["summarize", "summarized", "summarizes", "summary", "summaries", "tldr", "tl;dr", "key points", "condense"]},
    "writing_ai":     {"emoji": "emoji.noto.writing-hand", "photo": "ai writing", "aliases": ["ai writing", "writes for you", "write", "writing assistant", "draft", "drafts", "copywriting", "copy", "content writing", "blog post", "blog posts"]},
    "content":        {"emoji": "emoji.noto.memo", "photo": "ai content", "aliases": ["content", "content creation", "content creator", "create content", "generated content", "social posts", "social media posts"]},
    "productivity":   {"emoji": "emoji.noto.rocket", "photo": "ai productivity", "aliases": ["productivity", "productive", "get more done", "save time", "saves time", "hours back", "efficiency", "efficient", "faster work", "do more"]},
    "cost":           {"emoji": "emoji.noto.money-bag", "photo": "ai cost", "aliases": ["cost", "costs", "price", "pricing", "expensive", "cheap", "affordable", "free tier", "per-token", "api cost", "api costs", "budget"]},
    "data":           {"emoji": "emoji.noto.card-index", "mono": "icon.ant-design.database-outlined", "colour": "icon.icon-park-color.database-code", "photo": "data", "aliases": ["your data", "data in", "data-driven", "big data", "data pipeline", "data pipelines", "your own data", "private data", "customer data"]},
    "model":          {"mono": "icon.icon-park-outline.brain", "emoji": "emoji.noto.brain", "colour": "icon.icon-park-color.brain", "photo": "ai model", "aliases": ["models", "ai model", "ai models", "the model", "a model", "model weights", "checkpoint", "checkpoints"]},
    "algorithm":      {"mono": "icon.carbon.network-4", "emoji": "emoji.noto.input-symbols", "photo": "algorithm", "aliases": ["algorithms", "the algorithm", "algorithmic", "logic"]},
    "prediction_ai":  {"emoji": "emoji.noto.crystal-ball", "photo": "ai prediction", "aliases": ["predict", "predicts", "predicted", "predicting", "prediction", "predictions", "predictive", "forecast", "forecasting", "forecasts", "anticipate"]},
    "fraud":          {"emoji": "emoji.noto.detective", "photo": "fraud detection", "aliases": ["fraud detection", "fraud", "detect fraud", "anomaly detection", "anomalies", "suspicious", "flagged"]},
    "medical_ai":     {"emoji": "emoji.noto.stethoscope", "photo": "ai healthcare", "aliases": ["healthcare", "medical", "diagnosis", "diagnose", "clinical", "patient", "patients", "health", "ai doctor", "radiology", "drug discovery"]},
    "education_ai":   {"emoji": "emoji.noto.graduation-cap", "photo": "ai education", "aliases": ["education", "learn", "learning", "tutor", "tutoring", "ai tutor", "teach", "teaching", "student", "students", "homework", "study"]},
    "legal_ai":       {"emoji": "emoji.noto.balance-scale", "photo": "legal ai", "aliases": ["legal", "lawyer", "lawyers", "law firm", "contract review", "legal documents", "compliance check"]},
    "customerservice": {"emoji": "emoji.noto.telephone", "photo": "ai customer service", "aliases": ["customer service", "customer support", "support", "support agent", "help desk", "helpdesk", "customer experience", "csat", "ticket", "tickets", "resolve"]},
    "marketing_ai":   {"emoji": "emoji.noto.megaphone", "photo": "ai marketing", "aliases": ["marketing", "marketer", "ads", "advertising", "ad copy", "campaign", "campaigns", "seo", "social media", "growth"]},
    "sales_ai":       {"emoji": "emoji.noto.money-bag", "photo": "ai sales", "aliases": ["sales", "sell", "selling", "pipeline", "leads", "lead generation", "crm", "outreach", "cold email"]},
    "coding_ai":      {"emoji": "emoji.noto.laptop", "mono": "icon.icon-park-outline.code-computer", "colour": "icon.icon-park-color.code-computer", "photo": "ai coding", "aliases": ["coding", "code", "programming", "software development", "developer tools", "write software", "build apps", "ship code", "engineering"]},
    "design_ai":      {"emoji": "emoji.noto.artist-palette", "photo": "ai design", "aliases": ["design", "designs", "designer", "designers", "ui", "ux", "logo", "logos", "branding", "graphics", "mockup", "mockups"]},
    "science_ai":     {"emoji": "emoji.noto.microscope", "photo": "ai science", "aliases": ["science", "research", "researchers", "scientific", "discovery", "discover", "breakthrough", "breakthroughs", "experiment", "experiments", "lab", "laboratory", "protein folding", "alphafold"]},
    "startup_ai":     {"emoji": "emoji.noto.rocket", "mono": "icon.icon-park-outline.rocket", "photo": "ai startup", "aliases": ["startup", "startups", "ai startup", "ai startups", "ai company", "ai companies", "founded", "founder", "founders", "raise", "raised", "funding", "valuation", "unicorn", "ipo"]},
    "jobimpact":      {"emoji": "emoji.noto.briefcase", "photo": "ai jobs", "aliases": ["jobs", "job", "layoffs", "replaced by ai", "ai taking jobs", "workforce", "reskilling", "upskilling", "future of work", "automation risk", "replace workers"]},
    "ethics":         {"emoji": "emoji.noto.balance-scale", "photo": "ai ethics", "aliases": ["ethics", "ethical", "ethical ai", "ai ethics", "responsible", "responsibly", "moral", "morality"]},
    "openweight":     {"emoji": "emoji.noto.open-book", "photo": "open weights model", "aliases": ["open weights", "open weight", "open-weights", "downloadable model", "self-hosted model", "run it yourself"]},
    "api_ai":         {"mono": "icon.carbon.api", "emoji": "emoji.noto.desktop-computer", "photo": "ai api", "aliases": ["ai api", "api access", "api key", "api keys", "developer api", "rest api", "endpoint", "endpoints", "integrate ai", "ai integration", "api pricing"]},
    "multimodal":     {"emoji": "emoji.noto.sparkles", "photo": "multimodal ai", "aliases": ["multimodal", "multi-modal", "omni", "text image audio", "sees and hears", "understands images", "vision and audio", "text and images"]},
    "reasoning":      {"emoji": "emoji.noto.thought-balloon", "photo": "ai reasoning", "aliases": ["reasoning", "thinks", "thinking", "reasoning model", "chain of thought", "chain-of-thought", "cot", "reasons", "step by step", "test-time compute", "extended thinking"]},
    "longcontext":    {"emoji": "emoji.noto.books", "photo": "long context", "aliases": ["long context", "million token", "million-token", "entire codebase", "whole document", "long documents", "large documents"]},
    "realtime_ai":    {"emoji": "emoji.noto.high-voltage", "photo": "realtime ai", "aliases": ["real-time", "real time", "realtime", "live", "streaming", "low latency", "instant response", "responds instantly", "sub-second"]},
    "voice_mode":     {"emoji": "emoji.noto.speaker-high-volume", "photo": "voice ai", "aliases": ["voice mode", "voice assistant", "talk to", "voice conversation", "speech to speech", "voice ai", "spoken"]},
    "monitoring":     {"emoji": "emoji.noto.eyes", "photo": "ai monitoring", "aliases": ["monitor", "monitors", "monitored", "observability", "tracing", "traces", "logs", "evals in prod", "model monitoring", "drift"]},
    "benchmark_ai":   {"emoji": "emoji.noto.trophy", "photo": "ai benchmark", "aliases": ["sota", "state of the art", "state-of-the-art", "best model", "best performing", "tops the leaderboard", "mmlu", "swe-bench", "arena", "elo"]},
    "deepfake":       {"emoji": "emoji.noto.performing-arts", "photo": "deepfake", "aliases": ["deepfakes", "deep fake", "deep fakes", "face swap", "faceswap", "fake video", "synthetic media", "impersonation"]},
    "aiwatermark":    {"emoji": "emoji.noto.label", "photo": "ai detection", "aliases": ["ai detector", "detect ai content", "ai-generated content", "is it ai", "made by ai"]},
    "robotaxi":       {"emoji": "emoji.noto.oncoming-taxi", "photo": "robotaxi", "aliases": ["robo taxi", "robo-taxi", "driverless taxi", "waymo"]},
    "smart_home":     {"emoji": "emoji.noto.radio", "photo": "smart home ai", "aliases": ["smart home", "home automation", "smart speaker", "alexa", "google home", "home assistant"]},
    "wearable":       {"emoji": "emoji.noto.watch", "photo": "ai wearable", "aliases": ["wearable", "wearables", "smart glasses", "smartwatch", "ai pin", "smart ring"]},
    "ai_avatar_video": {"emoji": "emoji.noto.movie-camera", "photo": "ai presenter video", "aliases": ["ai presenter", "ai spokesperson", "ai presenter video", "video avatar", "talking avatar", "talking head video", "presenter video", "avatar video"]},
    "localization":   {"emoji": "emoji.noto.globe-with-meridians", "photo": "ai localization", "aliases": ["localization", "localisation", "localize", "dubbing", "dubbed", "subtitle", "subtitles", "captions"]},
    "upscaling":      {"emoji": "emoji.noto.magnifying-glass-tilted-left", "photo": "ai upscaling", "aliases": ["upscale", "upscaled", "upscaling", "super resolution", "enhance", "enhanced", "enhancement", "denoise", "restoration", "restore", "remaster"]},
    "styletransfer":  {"emoji": "emoji.noto.artist-palette", "photo": "style transfer", "aliases": ["style transfer", "restyle", "in the style of", "artistic style", "apply a style"]},
    "controlnet":     {"emoji": "emoji.noto.control-knobs", "photo": "controlnet", "aliases": ["controlnet", "lora", "dreambooth", "ip-adapter", "comfyui", "comfy ui", "automatic1111", "a1111"]},
    "consistency":    {"emoji": "emoji.noto.check-mark", "photo": "character consistency", "aliases": ["consistent character", "character consistency", "same character", "consistent style", "brand consistency"]},
    "storyboard":     {"emoji": "emoji.noto.film-frames", "photo": "storyboard", "aliases": ["storyboard", "storyboards", "scene", "scenes", "shot", "shots", "sequence", "sequences", "storyline", "narrative"]},
    "prompt_engineering2": {"emoji": "emoji.noto.memo", "photo": "prompt engineering", "aliases": ["better prompts", "prompt tips", "prompt tricks", "prompt library", "prompt template"]},
    "finetune_custom": {"emoji": "emoji.noto.control-knobs", "photo": "custom ai model", "aliases": ["custom ai model", "bespoke model", "your own model", "proprietary model", "private model"]},
    "opensource_data": {"emoji": "emoji.noto.open-book", "photo": "open data", "aliases": ["open data", "public dataset", "research data"]},
    "aitools":        {"emoji": "emoji.noto.toolbox", "mono": "icon.ant-design.tool-outlined", "colour": "icon.icon-park-color.tool", "photo": "ai tools", "aliases": ["ai tools", "ai tool", "toolset", "ai stack", "toolchain"]},
    "aitakeoff":      {"emoji": "emoji.noto.rocket", "photo": "ai takeoff", "aliases": ["ai boom", "ai hype", "ai revolution", "ai era", "age of ai", "ai wave", "ai race", "arms race"]},
    "aiworkflow":     {"emoji": "emoji.noto.clockwise-vertical-arrows", "photo": "ai workflow", "aliases": ["ai workflow", "ai workflows", "pipeline", "pipelines", "orchestration", "ai pipeline", "end to end", "end-to-end"]},
    "feature":        {"emoji": "emoji.noto.sparkles", "photo": "ai feature", "aliases": ["feature", "features", "capability", "capabilities", "can now", "now able to", "new feature"]},
    "limitations":    {"emoji": "emoji.noto.warning", "photo": "ai limitations", "aliases": ["limitations", "limitation", "cannot", "can't", "fails at", "struggles", "weakness", "weaknesses", "edge cases"]},
    "roadmap_ai":     {"emoji": "emoji.noto.world-map", "photo": "ai roadmap", "aliases": ["roadmap", "what's next", "coming soon", "next release", "upcoming", "future"]},
    "demo":           {"emoji": "emoji.noto.clapper-board", "photo": "ai demo", "aliases": ["demo", "demos", "live demo", "see it in action", "try it", "try it yourself", "hands on", "playground"]},
    "waitlist_ai":    {"emoji": "emoji.noto.hourglass-not-done", "photo": "waitlist", "aliases": ["waitlist", "beta", "early access", "preview", "private beta", "sign up early"]},
    "announce":       {"emoji": "emoji.noto.megaphone", "photo": "ai announcement", "aliases": ["announce", "announced", "announces", "announcing", "launch", "launched", "release", "released", "releasing", "unveiled", "unveils", "debuts", "ships", "shipped", "rolls out", "rollout", "rolling out"]},
    "pricing_ai":     {"emoji": "emoji.noto.label", "photo": "ai pricing", "aliases": ["pricing", "price", "costs", "subscription", "per month", "free", "free tier", "open source", "enterprise", "per seat", "usage-based"]},
    "competition_ai": {"emoji": "emoji.noto.vs-button", "photo": "ai competition", "aliases": ["versus", "vs", "compared to", "comparison", "beats", "outperforms", "better than", "faster than", "competitors", "rivals", "alternative", "alternatives"]},
}

VOCAB = {**CRYPTO, **AI}

# entries with no icon refs at all get the domain default so every key in the
# bank renders in every style (verified ids in both registries)

# emoji / fluent refs cannot satisfy the colour family (compiler enforces one
# native colour pack per film -> icon.icon-park-color); translate by asset name
EMOJI_TO_COLOUR = {"airplane": "airplane", "alarm-clock": "alarm-clock", "artist-palette": "color-card", "atom-symbol": "experiment", "automobile": "car", "oncoming-automobile": "car", "oncoming-taxi": "taxi", "balance-scale": "balance", "ballot-box-with-ballot": "checklist", "bank": "bank", "bar-chart": "analysis", "bear": "bear", "books": "book-open", "brain": "brain", "briefcase": "briefcase", "bubbles": "comment", "building-construction": "building-one", "bullseye": "aiming", "bust-in-silhouette": "avatar", "calendar": "calendar", "camera": "camera", "candle": "chart-stock", "card-file-box": "box", "chains": "link", "chart-decreasing": "chart-stock", "chart-increasing": "analysis", "check-box-with-check": "checklist", "check-mark": "check", "check-mark-button": "check", "clapper-board": "film", "clipboard": "clipboard", "clockwise-vertical-arrows": "cycle", "coin": "paper-money", "control-knobs": "config", "cross-mark": "close", "crown": "crown", "crystal-ball": "magic", "cyclone": "wind", "desktop-computer": "computer", "detective": "search", "dizzy": "dizzy-face", "face-in-clouds": "dizzy-face", "dog": "dog", "dollar-banknote": "paper-money", "down-arrow": "arrow-down", "droplet": "water", "ear-of-corn": "paper-money", "eye": "eyes", "eyes": "eyes", "fast-forward-button": "arrow-right", "film-frames": "film", "fire": "fire", "flying-saucer": "drone", "fork-and-knife": "fork", "framed-picture": "picture", "free-button": "label", "frog": "frog", "fuel-pump": "power", "full-moon": "moon", "gear": "setting", "gem-stone": "diamond", "ghost": "ghost", "globe-with-meridians": "globe", "glowing-star": "star", "graduation-cap": "school", "hammer-and-pick": "hammer-and-anvil", "hammer-and-wrench": "hammer-and-anvil", "handshake": "cooperative-handshake", "high-voltage": "lightning", "hourglass-not-done": "hourglass", "identification-card": "id-card", "input-symbols": "keyboard", "japanese-secret-button": "key", "key": "key", "old-key": "key-one", "label": "label", "laptop": "laptop", "ledger": "book-open", "left-arrow": "arrow-left", "left-right-arrow": "exchange", "right-arrow": "arrow-right", "link": "link", "lizard": "frog", "locked": "lock", "locked-with-key": "lock-one", "magnifying-glass-tilted-left": "search", "right-pointing-magnifying-glass": "search", "megaphone": "announcement", "memo": "file-editing", "microphone": "microphone", "microscope": "microscope", "mobile-phone": "phone", "money-bag": "paper-money", "money-with-wings": "paper-money-two", "movie-camera": "film", "musical-note": "music", "newspaper": "page", "no-entry": "caution", "open-book": "book-open", "package": "box", "page-facing-up": "page", "pancakes": "cooking-pot", "performing-arts": "star", "person": "avatar", "pick": "hammer-and-anvil", "pig-face": "pig", "potable-water": "water", "puzzle-piece": "puzzle", "radio": "broadcast-radio", "rainbow": "star", "raising-hands": "hands", "receipt": "bill", "red-question-mark": "help", "repeat-button": "cycle", "right-pointing": "arrow-right", "robot": "robot", "rocket": "rocket", "roll-of-paper": "page", "scissors": "scissors", "scroll": "agreement", "shark": "fish", "shopping-bags": "shopping", "shopping-cart": "shopping", "skull": "skull", "skull-and-crossbones": "skull", "slot-machine": "game", "snow-capped-mountain": "mountain", "sparkle": "star", "sparkles": "star", "speaker-high-volume": "speaker", "speech-balloon": "comment", "thought-balloon": "comment", "stethoscope": "health", "telephone": "phone", "television": "monitor", "test-tube": "test-tube", "toolbox": "tool", "trophy": "trophy", "umbrella": "umbrella", "unicorn": "rocking-horse", "video-game": "game", "vs-button": "contrast-view", "warning": "caution", "watch": "watch", "whale": "whale", "window": "browser", "world-map": "globe", "wrapped-gift": "gift", "writing-hand": "write", "chat-48": "communication", "cloud-48": "cloud-storage", "data-trending-48": "analysis"}

CRYPTO_DEFAULT = {"mono": "icon.mingcute.coin-line", "colour": "icon.icon-park-color.currency", "emoji": "emoji.noto.coin"}
AI_DEFAULT = {"mono": "icon.icon-park-outline.brain", "colour": "icon.icon-park-color.brain", "emoji": "emoji.noto.brain"}

# generic surface forms -> existing bank keys (everyday synonyms so plain
# speech resolves too; aliases for ambiguous words are avoided entirely)
PHRASE_EXTRA = {
    "bicycle": "bicycle", "bike": "bicycle", "bikes": "bicycle", "cycling": "bicycle",
    "cyclist": "bicycle", "motorbike": "motorcycle", "cars": "car", "vehicle": "car",
    "vehicles": "car", "automobile": "car", "buses": "bus", "trains": "train",
    "subway": "train", "metro": "train", "planes": "plane", "flight": "plane",
    "flights": "plane", "airplane": "plane", "jet": "plane", "ships": "ship",
    "boat": "ship", "boats": "ship", "trucks": "truck", "lorry": "truck",
    "moped": "scooter", "shops": "shop", "shopping": "shop", "mall": "shop",
    "stores": "store", "funds": "money", "bucks": "money", "dogs": "dog",
    "puppy": "dog", "puppies": "dog", "cats": "cat", "kitten": "cat",
    "birds": "bird", "trees": "tree", "flowers": "flower", "lawn": "grass",
    "mountains": "mountain", "hiking": "mountain", "sunny": "sun",
    "sunshine": "sun", "lunar": "moon", "night": "moon", "stars": "star",
    "earth": "world", "planet": "world", "planets": "world", "global": "world",
    "worldwide": "world", "international": "world", "books": "book",
    "novel": "book", "novels": "book", "reading": "book", "library": "book",
    "textbook": "book", "movies": "video", "movie": "video", "film": "video",
    "films": "video", "cinema": "video", "clip": "video", "songs": "music",
    "song": "music", "playlist": "music", "phones": "phone", "smartphone": "phone",
    "mobile": "phone", "cameras": "camera", "photography": "camera", "photo": "camera",
    "picture": "camera", "computers": "computer", "laptop": "computer", "pc": "computer",
    "screens": "screen", "display": "screen", "monitors": "monitor",
    "keyboards": "keyboard", "headset": "headphones", "earphones": "headphones",
    "earbuds": "headphones", "airpods": "headphones", "mics": "mic",
    "speakers": "speaker", "printers": "printer", "wifi": "router",
    "doors": "door", "windows": "window", "beds": "bed", "bedroom": "bed",
    "couch": "sofa", "couches": "sofa", "desk": "table", "pillows": "pillow",
    "umbrellas": "umbrella", "shirts": "shirt", "tshirt": "shirt",
    "dresses": "dress", "shoes": "shoe", "footwear": "shoe", "sneakers": "sneaker",
    "watches": "watch", "smartwatch": "watch", "sunglasses": "glasses",
    "eyewear": "glasses", "backpacks": "backpack", "rucksack": "backpack",
    "gifts": "gift", "present": "gift", "presents": "gift", "trophies": "trophy",
    "award": "trophy", "awards": "trophy", "medal": "trophy", "medals": "trophy",
    "flags": "flag", "keys": "key", "locks": "lock", "padlock": "lock",
    "locked": "lock", "hammer": "tools", "screwdriver": "tools",
    "healthcare": "health", "medical": "health", "wellness": "health",
    "hospitals": "hospital", "clinic": "hospital", "clinics": "hospital",
    "pills": "pill", "medicine": "pill", "medication": "pill",
    "injections": "syringe", "injection": "syringe", "jab": "syringe",
    "vaccines": "vaccine", "vaccination": "vaccine", "immunization": "vaccine",
    "bandages": "bandage", "first aid": "bandage", "injury": "bandage",
    "doctor": "stethoscope", "doctors": "stethoscope", "checkup": "stethoscope",
    "loaf": "bread", "bakery": "bread", "baking": "bread", "latte": "coffee",
    "cappuccino": "coffee", "cafe": "coffee", "job": "work", "jobs": "work",
    "career": "work", "careers": "work", "employee": "worker", "employees": "worker",
    "staff": "worker", "colleague": "team", "colleagues": "team", "teams": "team",
    "teammates": "team", "business": "company", "startup": "company",
    "corporation": "company", "built": "build", "constructed": "build",
    "making": "build", "developer": "engineer", "dev": "engineer",
    "programmer": "engineer", "dreams": "dream", "goal": "target",
    "goals": "target", "aim": "target", "objective": "target", "grow": "growth",
    "growing": "growth", "increase": "growth", "find": "search",
    "looking for": "search", "discover": "search", "danger": "warning",
    "caution": "warning", "beware": "warning", "alert": "warning",
    "ideas": "idea", "insight": "idea", "launching": "launch", "debut": "launch",
    "winning": "win", "winner": "win", "victory": "win", "success": "win",
    "weekly": "week", "monthly": "month", "yearly": "year", "weeks": "week",
    "months": "month", "years": "year", "trip": "travel", "trips": "travel",
    "vacation": "travel", "journey": "travel", "games": "game",
    "gaming": "game", "coding": "code", "programming": "code",
    "software": "code", "program": "code", "script": "code", "scripts": "code",
    "apps": "app", "application": "app", "products": "product", "item": "product",
    "charts": "chart", "graph": "chart", "graphs": "chart", "documents": "document",
    "paperwork": "document", "file": "document", "files": "document",
    "folders": "folder", "lights": "light", "lamp": "light",
    "electricity": "power", "energy": "power", "batteries": "battery",
    "sensors": "sensor", "drones": "drone", "robots": "robot",
    "artificial intelligence": "ai", "offices": "office", "workplace": "office",
    "hotels": "hotel", "buildings": "building", "skyscraper": "building",
    "factories": "factory", "manufacturing": "factory", "campsite": "tent",
    "camping": "tent", "farm": "tractor", "farming": "tractor",
    "agriculture": "tractor", "dairy": "milk", "teeth": "tooth",
    "dentist": "tooth", "dental": "tooth", "yard": "grass", "forest": "tree",
    "bouquet": "flower", "dinner": "pantry", "lunch": "pantry", "meal": "pantry",
    "food": "pantry", "groceries": "pantry", "eat": "pantry", "eating": "pantry",
    "cook": "pantry", "cooked": "pantry", "cooking": "pantry", "kitchen": "pantry",
    "friends": "people", "folks": "people", "crowd": "people", "persons": "people",
    "individual": "person", "someone": "person", "anyone": "person",
    "guy": "person", "guys": "person", "man": "person", "woman": "person",
    "lady": "person", "kid": "person", "child": "person", "children": "people",
    "boy": "person", "girl": "person", "baby": "person", "human": "person",
    "friend": "people", "buddy": "people", "family": "people",
    "home": "home", "house": "house", "houses": "house", "housing": "house",
    "apartment": "home", "dollars": "dollar", "cash": "cash",
}

def load_ids():
    mono = {a["id"] for a in json.load(open(COMMUNITY / "icons-registry.json"))["assets"]}
    colour = {a["id"] for a in json.load(open(COMMUNITY / "colour-registry.json"))["assets"]}
    return mono, colour

def norm(s):
    return re.sub(r"[^a-z0-9']", "", s.lower())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()

    mono_ids, colour_ids = load_ids()
    doc = json.load(open(STYLES))
    bank = doc["entity_bank"]

    errors, added, skipped, filled = [], [], [], []
    phrases = {}
    for key, spec in VOCAB.items():
        base = bank.get(key, {})
        entry = dict(base)
        changed = False
        for fam in ("colour", "mono", "emoji"):
            ref = spec.get(fam)
            if ref:
                pool = mono_ids if fam == "mono" else colour_ids
                if ref not in pool:
                    errors.append(f"{key}.{fam}: {ref} not in registry")
                    continue
                if not base.get(fam):
                    entry[fam] = ref
                    changed = True
        if spec.get("photo") and not base.get("photo"):
            entry["photo"] = spec["photo"]
            changed = True
        # every entry must render in every style: photo-only entries get a
        # domain-default icon set. The colour family is one native pack per
        # film (compiler ASSET_PACK_MIX gate -> icon.icon-park-color, brand
        # marks exempt), so emoji/fluent colour refs are translated into that
        # pack by asset name; unresolved names get the domain default colour.
        dom = AI_DEFAULT if spec in AI.values() else CRYPTO_DEFAULT
        if not any(entry.get(f) for f in ("colour", "mono", "emoji")):
            for fam, ref in dom.items():
                entry[fam] = ref
                changed = True

        def _park(ref):
            if not ref:
                return None
            if ref.startswith(("icon.icon-park-color.", "brand.")):
                return ref
            mapped = EMOJI_TO_COLOUR.get(ref.split(".")[-1])
            return "icon.icon-park-color." + mapped if mapped else None

        new_colour = _park(entry.get("colour")) or _park(entry.get("emoji")) or dom["colour"]
        if new_colour != entry.get("colour"):
            entry["colour"] = new_colour
            changed = True
        if not entry:
            errors.append(f"{key}: no refs resolved")
            continue
        if key not in bank:
            bank[key] = entry
            added.append(key)
        elif changed:
            bank[key] = entry
            filled.append(key)
        else:
            skipped.append(key)
        for a in spec.get("aliases", []):
            a = a.strip()
            if a and a != key:
                phrases[a] = key
        # canonical key itself: multiword keys and collision-safe singles alike
        if " " in key or key not in bank:
            phrases[key] = key

    # generic synonyms onto existing keys; a target that isn't in the bank is a
    # typo, so fail loudly rather than write a dead phrase
    for alias, key in PHRASE_EXTRA.items():
        if key not in bank:
            errors.append(f"phrase '{alias}' -> '{key}': target not in entity_bank")
            continue
        phrases[alias] = key

    # ---- fill missing families on pre-existing entries --------------------
    # Many legacy entries are photo-only (invisible in 5 of 6 styles). Resolve
    # each missing family by asset name: colour stays inside icon.icon-park-color
    # (the film's single native pack), mono may come from any icon pack, emoji
    # from any emoji pack. Never overwrites an existing ref.
    SYN = {
        "access": "key", "almond": "macadamia-nut", "bandage": "first-aid-kit",
        "battery": "battery-full", "bed": "bedside", "bicycle": "bike",
        "butter": "bread", "cable": "plug", "cereal": "bowl", "chocolate": "candy",
        "coffee": "coffee-machine", "crane": "building-one", "document": "page",
        "door": "gate", "dress": "full-dress-longuette", "espresso": "coffee-machine",
        "ferry": "ship", "flower": "blossom", "grass": "leaf", "guitar": "music",
        "headphones": "headset", "lavender": "blossom", "mic": "microphone",
        "motorcycle": "bike", "pantry": "box", "pillow": "bedside",
        "plane": "airplane", "quartz": "diamond", "safe": "safe-retrieval",
        "scooter": "bike", "secure": "lock", "sensor": "chip",
        "shirt": "clothes-turtleneck", "shoe": "clothes-skates",
        "sneaker": "clothes-skates", "sourdough": "bread", "sugar": "candy",
        "syringe": "injection", "tablet": "monitor", "thermostat": "power",
        "tooth": "teeth", "tractor": "truck", "travel": "airplane",
        "vaccine": "pill", "vinyl": "music", "violin": "music",
        "warning": "caution", "wine": "cocktail", "wrench": "tool",
        "yogurt": "milk",
    }
    old_filled = {"colour": 0, "mono": 0, "emoji": 0}

    # emoji-family aliases for keys whose name differs from the emoji name
    EMOJI_SYN = {
        "car": "automobile", "tree": "evergreen-tree", "vinyl": "optical-disk",
        "health": "red-heart", "shirt": "t-shirt", "shoe": "mans-shoe",
        "sneaker": "running-shoe", "sleep": "zzz", "sofa": "couch-and-lamp",
        "table": "chair", "wine": "wine-glass", "tea": "teapot",
        "milk": "glass-of-milk", "cheese": "cheese-wedge",
        "monitor": "desktop-computer", "sensor": "satellite-antenna",
        "router": "satellite-antenna", "cable": "electric-plug",
        "scooter": "motor-scooter", "truck": "delivery-truck",
        "crane": "building-construction", "grass": "herb",
        "rice": "cooked-rice", "cereal": "bowl-with-spoon",
        "pantry": "file-cabinet", "piano": "musical-keyboard",
        "speaker": "speaker-high-volume", "thermostat": "thermometer",
        "tablet": "mobile-phone", "quartz": "gem-stone",
        "yogurt": "cup-with-straw", "espresso": "hot-beverage",
        "apple": "red-apple", "almond": "chestnut", "bandage": "adhesive-bandage",
        "pillow": "bed", "coffee": "hot-beverage", "sourdough": "bread",
        "butter": "bread",
    }

    def name_cands(k):
        out = [k]
        if k.endswith("s"):
            out.append(k[:-1])
        else:
            out.append(k + "s")
        if k in SYN:
            out.insert(0, SYN[k])
        return out

    def _by_short(pool, prefixes):
        idx = {}
        order = {p: i for i, p in enumerate(prefixes)}
        for iid in pool:
            for pre in prefixes:
                if iid.startswith(pre):
                    short = iid[len(pre):]
                    if short not in idx or order[pre] < idx[short][0]:
                        idx[short] = (order[pre], iid)
        return {s: i for s, (o, i) in idx.items()}

    COLOUR_IDX = _by_short(colour_ids, ("icon.icon-park-color.",))
    MONO_IDX = _by_short(mono_ids, ("icon.icon-park-outline.", "icon.lucide.",
                                    "icon.mingcute.", "icon.carbon.", "icon.tabler.",
                                    "icon.healthicons.", "icon.ri.", "icon.ant-design."))
    EMOJI_IDX = _by_short(colour_ids, ("emoji.noto.", "emoji.fluent.", "emoji.fluent-flat."))
    FAM_IDX = {"colour": COLOUR_IDX, "mono": MONO_IDX, "emoji": EMOJI_IDX}

    for k, v in bank.items():
        if k in VOCAB:
            continue
        spec_changed = False
        for fam in ("colour", "mono", "emoji"):
            if v.get(fam):
                continue
            hit = next((FAM_IDX[fam][c] for c in name_cands(k) if c in FAM_IDX[fam]), None)
            if hit:
                v[fam] = hit
                spec_changed = True
                old_filled[fam] += 1
        if spec_changed:
            filled.append(k + ":legacy")

    DOMAIN_EMOJI = {**{k: AI_DEFAULT["emoji"] for k in AI},
                    **{k: CRYPTO_DEFAULT["emoji"] for k in CRYPTO}}
    for k, v in bank.items():
        if v.get("emoji"):
            continue
        if (v.get("colour") or "").startswith("brand."):
            continue  # brand marks render in emoji style and are pack-exempt
        cands = ([EMOJI_SYN[k]] if k in EMOJI_SYN else []) + name_cands(k)
        hit = next((EMOJI_IDX[c] for c in cands if c in EMOJI_IDX), None)
        v["emoji"] = hit or DOMAIN_EMOJI.get(k, "emoji.noto.sparkles")
        old_filled["emoji"] += 1
        if k + ":legacy" not in filled:
            filled.append(k + ":legacy")

    if errors:
        print("REF ERRORS:", file=sys.stderr)
        for e in errors:
            print("  " + e, file=sys.stderr)
        sys.exit(1)

    phrases = {k: v for k, v in phrases.items() if k.strip()}
    doc["entity_phrases"] = dict(sorted(phrases.items()))
    out = json.dumps(doc, indent=1)
    if args.report:
        print(f"added {len(added)} entries, filled {len(filled)}, skipped {len(skipped)} existing, {len(phrases)} phrases")
        for k in sorted(added):
            print(f"  {k}: {json.dumps(bank[k])}")
        return
    STYLES.write_text(out + "\n")
    print(f"styles.json: +{len(added)} bank entries (total {len(bank)}), {len(phrases)} phrase forms; filled {len(filled)}, skipped {len(skipped)} existing")

if __name__ == "__main__":
    main()
