// importing the required modules
const express = require('express'); // to create the server
const app = express(); // initiating the app
const path = require('path'); // to work with directory/file path

// took help from chatgpt here, originally using axios but it was giving me error even after multiple err handling
// chat suggested i use node-fetch instead 
const fetch = (...args) => import('node-fetch').then(({ default: fetch }) => fetch(...args));

app.set('view engine', 'ejs'); // .ejs templating module
app.set('views', path.join(__dirname, 'views'));  //.ejs directory template location
app.use(express.static(path.join(__dirname, 'public'))); //middleware to handle the css styling from the public folder
app.use(express.urlencoded({ extended: true })); // middleware to parse data 

// home screen handling
app.get('/', (req, res) => res.render('index'));

// View Books
app.get('/books', async (req, res) => {
  try { // fetches the book from the backend api
    const response = await fetch('http://127.0.0.1:5000/api/books');
    if (!response.ok) throw new Error(`Fetch failed: ${response.status} ${response.statusText}`);
    const books = await response.json();  // changes the respionse to JSON
    res.render('books', { books }); // renders books.ejs with books data
  } catch (err) { // fallback if an error occurs 
    console.error('Error fetching books:', err.message);
    res.render('books', { books: [] });
  }
});

// view customer handling
app.get('/customers', async (req, res) => {
  try {
    const response = await fetch('http://127.0.0.1:5000/api/customers');
    const customers = await response.json(); // gets customer data from backend
    res.render('customers', { customers }); // renders .ejs file
  } catch (err) {
    console.error('Error fetching customers:', err.message); // fallback incase of error 
    res.render('customers', { customers: [] });
  }
});

// borrow books handling
app.get('/borrow', async (req, res) => {
  try {
    const booksRes = await fetch('http://127.0.0.1:5000/api/books'); // fetches the available books
    const customersRes = await fetch('http://127.0.0.1:5000/api/customers'); // fetches the available customers
    const books = await booksRes.json();
    const customers = await customersRes.json(); // renders the borrow form
    res.render('borrow', { books, customers });
  } catch (err) {
    console.error('Error loading borrow form:', err.message); // error control 
    res.render('borrow', { books: [], customers: [] });
  }
});

// handles submission when borrowing a book
app.post('/borrow', async (req, res) => {
  try {
    await fetch('http://127.0.0.1:5000/api/borrow', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        bookid: req.body.bookid,
        customerid: req.body.customerid
      })
    });
    res.redirect('/');  // redirect after borrow
  } catch (err) {
    console.error('Error borrowing book:', err.message); // error handling 
    res.status(500).send('Error borrowing book');
  }
});

// return book handling
app.get('/return', async (req, res) => {
  try {
    const response = await fetch('http://127.0.0.1:5000/api/borrowings');
    const borrowings = await response.json();
    res.render('return', { borrowings }); // rendering the return form
  } catch (err) {
    console.error('Error loading return form:', err.message);
    res.render('return', { borrowings: [] }); // error control
  }
});

// handling to return a book
app.post('/return', async (req, res) => {
  try {
    await fetch('http://127.0.0.1:5000/api/return', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: req.body.id })
    });
    res.redirect('/'); // redirect after return
  } catch (err) {
    console.error('Error returning book:', err.message);
    res.status(500).send('Error returning book');
  }
});

// borrowing records handle
app.get('/borrowings', async (req, res) => {
  try {
    const response = await fetch('http://127.0.0.1:5000/api/borrowings');
    const records = await response.json();
    res.render('borrowings', { records }); // renders the borrow records 
  } catch (err) {
    console.error('Error fetching borrowings:', err.message);
    res.render('borrowings', { records: [] }); // error handling
  }
});
// server to connect to the port
app.listen(3000, () => {
  console.log('Frontend running at http://localhost:3000');
});
