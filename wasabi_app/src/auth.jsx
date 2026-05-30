import { useState, useRef, useEffect } from 'react'
import apiCall from './backendConfig.jsx'

function Auth(props) {
  const [authors, set_authors] = useState([])
  const [show_login, set_show_login] = useState(false)

  const update_authors = () => {
    apiCall({ route: "get_authors" })
      .then(apiResponse => apiResponse.data)
      .then((data) => {
        console.log("authors recieved: ", data)
        set_authors(Array.from(data))
        console.log("authors set: ", authors)
      })
  }


  const is_anon = props.author === "anon"
  const login_text = is_anon ? "log in" : "change user"

  const change_author = (event) => {
    set_show_login(false)
    props.set_author(event.target.id)
  }


  const new_author_name = useRef("")

  useEffect(() => {
    console.log(new_author_name)
    console.log(authors)
  }, [authors, new_author_name])

  const new_author = () => {
    apiCall({ route: "new_author", body: { name: new_author_name.current } })
    props.set_author(new_author_name.current)
    set_show_login(false)
  }

  useEffect(() => {
    update_authors()
  }, [])

  return <>
    <div style={{ visibility: show_login ? 'visible' : 'hidden' }}>
      who are you?
      <div>
        {authors.map(name => (
          <div>
            <button id={name} onClick={change_author}>{name}</button>
          </div>
        ))}
      </div>
      <div>
        or add a new author:
        <button onClick={new_author}>submit</button>
        <input placeholder='name' onInput={(e) => { new_author_name.current = e.target.value }} />
      </div>
    </div >

    <button
      style={{ visibility: !show_login ? 'visible' : 'hidden' }}
      onClick={() => { set_show_login(true) }}
    >login</button>
  </>
}
export default Auth
