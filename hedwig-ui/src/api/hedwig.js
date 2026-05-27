const BASE =''

async function req(methd, path, body)
{
    const opts = {
        method , 
        headers : {'Content-Type': 'application/json'},
    }

    if (body) opts.body = JSON.stringify(body)
    const res = await fetch(BASE + path , opts)

    return res.json()
} 

export const getSetupStatus = () => req('GET','api/setup/status')
export const connectWhatsApp = (instance_id , api_token) => req('POST','/api/setup/whatsapp' ,{instance_id, api_token})
export const getContacts = () => req('GET' , '/api/setup/trusted-contacts')
export const addContacts = (name , phone) => req('POST' , '/api/setup/trusted-contact' , {name, phone})
export const removeContact = (name)=> req('DELETE' , '/api/setup/trusted-contact', { name })
export const getLogs = () => req('GET', '/api/logs')