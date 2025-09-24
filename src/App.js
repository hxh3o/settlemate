import './App.css';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import LandingPage from './screens/LandingPage.js';
import Test from './screens/test.js';
import Login from './screens/login.js';
import SignUp from './screens/signup.js';
import Profile from './screens/profile.js';
import EditProfile from './screens/editprofile.js';
import Trip from './screens/trip.js';
import Transactions from './screens/transactions.js';
import Transaction from './screens/transaction.js';
import Transfers from './screens/transfers.js';
import EditTransaction from './screens/edittransaction.js';
import EditTrip from './screens/edittrip.js';
import Header from './screens/header';
import ForgotPassword from './screens/forgotPassword.js';
import Reset from './screens/reset.js';

function App() {
	return (
		<Router>
			<div className='myhtml'>
				<div className='main-header'>
					<Header />
				</div>
				<div className='main-content'>
					<Routes>
						<Route exact path='/' element={<LandingPage></LandingPage>}></Route>
						<Route exact path='/test' element={<Test></Test>}></Route>
						<Route exact path='/login' element={<Login></Login>}></Route>
						<Route exact path='/signup' element={<SignUp></SignUp>}></Route>
						<Route exact path='/forgotPassword' element={<ForgotPassword></ForgotPassword>}></Route>
						<Route exact path='/reset/:id' element={<Reset></Reset>}></Route>
						<Route exact path='/profile' element={<Profile></Profile>}></Route>
						<Route exact path='/editprofile' element={<EditProfile></EditProfile>}></Route>
						<Route exact path='/trip' element={<Trip></Trip>}></Route>
						<Route exact path='/transactions' element={<Transactions></Transactions>}></Route>
						<Route exact path='/transaction' element={<Transaction></Transaction>}></Route>
						<Route exact path='/transfer' element={<Transfers></Transfers>}></Route>
						<Route exact path='/edittransaction' element={<EditTransaction></EditTransaction>}></Route>
						<Route exact path='/edittrip' element={<EditTrip></EditTrip>}></Route>
					</Routes>
				</div>
				<ToastContainer />
			</div>
		</Router>
	);
}

export default App;
