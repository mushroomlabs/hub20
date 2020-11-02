import Decimal from 'decimal.js-light'

import Ethereum from './ethereum'

const BASE_URL = 'https://api.coingecko.com/api/v3'

const TOKEN_LOGO_URL = {
    ABT: "https://assets.coingecko.com/coins/images/2341/large/arcblock.png",
    ABYSS: "https://assets.coingecko.com/coins/images/2105/large/token_500.png",
    ADX: "https://assets.coingecko.com/coins/images/847/large/adex.png",
    APPC: "https://assets.coingecko.com/coins/images/1876/large/appcoins.png",
    AST: "https://assets.coingecko.com/coins/images/1019/large/AST.png",
    BAT: "https://assets.coingecko.com/coins/images/677/large/basic-attention-token.png",
    BBO: "https://assets.coingecko.com/coins/images/3795/large/bigbom-logo.png",
    BIX: "https://assets.coingecko.com/coins/images/1441/large/bibox-token.png",
    BLZ: "https://assets.coingecko.com/coins/images/2848/large/bluzelle.png",
    BNT: "https://assets.coingecko.com/coins/images/736/large/bancor.png",
    VGX: "https://assets.coingecko.com/coins/images/794/large/Voyager-vgx.png",
    CDT: "https://assets.coingecko.com/coins/images/1231/large/blox.png",
    CHAT: "https://assets.coingecko.com/coins/images/2568/large/chatcoin.png",
    CND: "https://assets.coingecko.com/coins/images/1006/large/cindicator.png",
    CNN: "https://assets.coingecko.com/coins/images/2787/large/cnn_logo_big.png",
    COFI: "https://assets.coingecko.com/coins/images/1709/large/coinfi.png",
    CVC: "https://assets.coingecko.com/coins/images/788/large/civic.png",
    DAI: "https://assets.coingecko.com/coins/images/1442/large/dai.png",
    DCC: "https://assets.coingecko.com/coins/images/4820/large/dcc-logo.png",
    DTH: "https://assets.coingecko.com/coins/images/2231/large/dether.png",
    DGX: "https://assets.coingecko.com/coins/images/4171/large/DGX_Token.png",
    DTA: "https://assets.coingecko.com/coins/images/2604/large/data.png",
    EDU: "https://assets.coingecko.com/coins/images/3256/large/educoin.jpg",
    EKO: "https://assets.coingecko.com/coins/images/2437/large/echolink.png",
    ELEC: "https://assets.coingecko.com/coins/images/3415/large/d45b1d82743c749d05697da200179874.jpg",
    ELF: "https://assets.coingecko.com/coins/images/1371/large/aelf-logo.png",
    ENG: "https://assets.coingecko.com/coins/images/1007/large/enigma-logo.png",
    ENJ: "https://assets.coingecko.com/coins/images/1102/large/enjin-coin-logo.png",
    EURS: "https://assets.coingecko.com/coins/images/5164/large/EURS_300x300.png",
    GEN: "https://assets.coingecko.com/coins/images/3479/large/gen.png",
    GNO: "https://assets.coingecko.com/coins/images/662/large/gnosis-logo.png",
    GTO: "https://assets.coingecko.com/coins/images/1359/large/gifto.png",
    INF: "https://assets.coingecko.com/coins/images/4719/large/inf.png",
    KNC: "https://assets.coingecko.com/coins/images/947/large/kyber-logo.png",
    LBA: "https://assets.coingecko.com/coins/images/3673/large/libra-credit.png",
    LEND: "https://assets.coingecko.com/coins/images/1365/large/ethlend.png",
    LINK: "https://assets.coingecko.com/coins/images/877/large/chainlink-new-logo.png",
    LRC: "https://assets.coingecko.com/coins/images/913/large/LRC.png",
    MKR: "https://assets.coingecko.com/coins/images/1364/large/maker.png",
    MANA: "https://assets.coingecko.com/coins/images/878/large/decentraland-mana.png",
    MAS: "https://assets.coingecko.com/coins/images/4287/large/MAS.png",
    MCO: "https://assets.coingecko.com/coins/images/739/large/mco.png",
    MDS: "https://assets.coingecko.com/coins/images/1343/large/medishares.png",
    MLN: "https://assets.coingecko.com/coins/images/605/large/melon.png",
    MOC: "https://assets.coingecko.com/coins/images/2374/large/moc.png",
    MOT: "https://assets.coingecko.com/coins/images/2225/large/olympus.png",
    MTL: "https://assets.coingecko.com/coins/images/763/large/metal.png",
    MYB: "https://assets.coingecko.com/coins/images/1240/large/mybit.png",
    NPXS: "https://assets.coingecko.com/coins/images/2170/large/pundi-x.png",
    OCN: "https://assets.coingecko.com/coins/images/2559/large/ocn.png",
    OMG: "https://assets.coingecko.com/coins/images/776/large/omisego.png",
    OST: "https://assets.coingecko.com/coins/images/1367/large/ost.jpg",
    PAL: "https://assets.coingecko.com/coins/images/3689/large/pal_logo_only_square_transparent.png",
    PAX: "https://assets.coingecko.com/coins/images/6013/large/paxos_standard.png",
    PAY: "https://assets.coingecko.com/coins/images/775/large/TenX-Icon-CircleBlack.png",
    POE: "https://assets.coingecko.com/coins/images/910/large/poet.png",
    POLY: "https://assets.coingecko.com/coins/images/2784/large/polymath-network.png",
    POWR: "https://assets.coingecko.com/coins/images/1104/large/power-ledger.png",
    PRO: "https://assets.coingecko.com/coins/images/869/large/propy.png",
    RCN: "https://assets.coingecko.com/coins/images/1057/large/ripio-credit-network.png",
    RDN: "https://assets.coingecko.com/coins/images/1132/large/raiden-logo.jpg",
    REN: "https://assets.coingecko.com/coins/images/3139/large/ren.png",
    REP: "https://assets.coingecko.com/coins/images/309/large/Webp.net-resizeimage_%288%29.png",
    REQ: "https://assets.coingecko.com/coins/images/1031/large/Request_icon.png",
    RLC: "https://assets.coingecko.com/coins/images/646/large/iExec_RLC.png",
    SALT: "https://assets.coingecko.com/coins/images/962/large/salt.png",
    SNT: "https://assets.coingecko.com/coins/images/779/large/status.png",
    SPN: "https://assets.coingecko.com/coins/images/2596/large/sapien.png",
    SSP: "https://assets.coingecko.com/coins/images/4642/large/smartshare.png",
    STORM: "https://assets.coingecko.com/coins/images/1369/large/storm.png",
    TTC: "https://assets.coingecko.com/coins/images/3214/large/ttc-protocol.png",
    UPP: "https://assets.coingecko.com/coins/images/3369/large/Sentinel_Protocol.jpg",
    USDC: "https://assets.coingecko.com/coins/images/6319/large/USD_Coin_icon.png",
    USDT: "https://assets.coingecko.com/coins/images/325/large/tether.png",
    WABI: "https://assets.coingecko.com/coins/images/1338/large/Tael.png",
    WAXP: "https://assets.coingecko.com/coins/images/1372/large/wax.png",
    WBTC: "https://assets.coingecko.com/coins/images/7598/large/wrapped_bitcoin_wbtc.png",
    WETH: "https://assets.coingecko.com/coins/images/2518/large/weth.png",
    WINGS: "https://assets.coingecko.com/coins/images/648/large/wings.png",
}


async function makeRequest(url) {
    let response = await fetch(url, {
        mode: 'cors'
    })

    return await response.json()
}


async function getEthereumRate(currencyCode) {
    let url = `${BASE_URL}/simple/price?ids=ethereum&vs_currencies=${currencyCode}`
    let data = await makeRequest(url)
    return data && Decimal(data.ethereum[currencyCode.toLowerCase()])
}

async function getRateByTokenAddress(tokenAddress, currencyCode) {
    let url = `${BASE_URL}/simple/token_price/ethereum?contract_addresses=${tokenAddress}&vs_currencies=${currencyCode}`
    let data = await makeRequest(url)

    // Attention: data will be keyed by token address (checksumed),
    // tokenAddress is not checksum. This is fine because the Object
    // will have only one item, so we can go straight to about the
    // object values
    let quotes = Object.values(data)
    return Decimal(quotes[0][currencyCode.toLowerCase()])

}

async function getTokenLogoUrlByAddress(tokenAddress) {
    let url = `${BASE_URL}/coins/ethereum/contract/${tokenAddress}`
    let data = await makeRequest(url)
    return data && data.image && data.image.large
}

async function getTokenLogo(token) {
    let url = TOKEN_LOGO_URL[token.code.toUpperCase()]

    if (url) {
        return url
    }

    let address = Ethereum.tokenAddresses[token.code]
    if (address) {
        return await getTokenLogoUrlByAddress(address)
    }

    return 'https://assets.coingecko.com/coins/images/279/large/ethereum.png'
}


async function getTokenRate(token, currencyCode) {

    if (token.network_id == Ethereum.networkIds.mainnet) {
        return await getRateByTokenAddress(token.address, currencyCode)
    }

    let address = Ethereum.tokenAddresses[token.code]
    if (address) {
        return await getRateByTokenAddress(address, currencyCode)
    }
    else {
        let ethRate = await getEthereumRate(currencyCode)
        return ethRate && ethRate.times(Math.random() * 100)
    }
}

export default { getEthereumRate, getTokenRate, getTokenLogo }
