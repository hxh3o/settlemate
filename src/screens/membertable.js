import { useEffect, useMemo, useState } from 'react';
import { MaterialReactTable, useMaterialReactTable } from 'material-react-table';
import { useNavigate, useLocation } from 'react-router-dom';
import Modal from '@mui/material/Modal';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import { toast } from 'react-toastify';
import { API, authHeaders } from '../api';

const style = {
	position: 'absolute',
	top: '50%',
	left: '50%',
	transform: 'translate(-50%, -50%)',
	width: 'auto',
	maxWidth: '50%',
	height: 'auto',
	maxHeight: '50%',
	bgcolor: 'background.paper',
	border: '2px solid #000',
	boxShadow: 24,
	p: 4,
	display: 'flex',
	justifyContent: 'center',
	alignItems: 'center',
	flexDirection: 'column',
};

const MemberTable = ({ tripid, ownerId }) => {
	const location = useLocation();
	const [data, setData] = useState([]);
	const [isError, setIsError] = useState(false);
	const [isLoading, setIsLoading] = useState(false);
	const [isRefetching, setIsRefetching] = useState(false);
	const [rowCount, setRowCount] = useState(0);
	const [modalOpen, setModal] = useState(false);
	const [content, setContent] = useState(0);
	const [user, setUser] = useState({ name: '', email: '', _id: '' });

	const [columnFilters, setColumnFilters] = useState([]);
	const [globalFilter, setGlobalFilter] = useState('');
	const [sorting, setSorting] = useState([]);
	const [pagination, setPagination] = useState({
		pageIndex: 0,
		pageSize: 5,
	});

	useEffect(() => {
		// Guard against missing/invalid tripid
		if (!tripid || typeof tripid !== 'string' || tripid.length < 10) {
			navigate('/');
			return;
		}
		const fetchData = async () => {
			if (!data.length) {
				setIsLoading(true);
			} else {
				setIsRefetching(true);
			}

            try {
                const response = await fetch(`${API}/getTripMembers`, {
                    method: 'POST',
                    headers: authHeaders(),
                    body: JSON.stringify({
                        tripid: tripid,
                    }),
                });
				const json = await response.json();
				if (json.success) {
					let notintrip = true;
					for (let i in json.data.members) {
						if (json.data.members[i]._id === json.myID) notintrip = false;
					}
					// if (notintrip) console.log('kicked');
					if (notintrip) navigate('/ ');
					// console.log(json.data);
					setData(json.data.members);
					setRowCount(json.data.members.length);
					if (json.newAuthToken) localStorage.setItem('authToken', json.newAuthToken);
				} else {
					localStorage.removeItem('authToken');
					localStorage.setItem('forcedLogOut', true);
					navigate('/profile');
				}
			} catch (error) {
				setIsError(true);
				console.error('Error fetching userData :', error);
				return;
			}
			setIsError(false);
			setIsLoading(false);
			setIsRefetching(false);
		};
		fetchData();
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, []);

	const columns = useMemo(
		() => [
			{
				accessorKey: 'name',
				header: 'Member Name',
			},
			{
				accessorKey: 'email',
				header: 'Member Email',
			},
		],
		[]
	);
	const navigate = useNavigate();
	const table = useMaterialReactTable({
		columns,
		data,
		enableRowSelection: false,
		enableColumnFilters: false,
		getRowId: row => row,
		initialState: { showColumnFilters: false },
		manualFiltering: false,
		manualPagination: false,
		manualSorting: false,
		muiToolbarAlertBannerProps: isError
			? {
					color: 'error',
					children: 'Error loading data',
			  }
			: undefined,
		onColumnFiltersChange: setColumnFilters,
		onGlobalFilterChange: setGlobalFilter,
		onPaginationChange: setPagination,
		onSortingChange: setSorting,
		rowCount,
		state: {
			columnFilters,
			globalFilter,
			isLoading,
			pagination,
			showAlertBanner: isError,
			showProgressBars: isRefetching,
			sorting,
		},
		muiTableBodyRowProps: ({ row }) => ({
			onClick: () => {
				if (location.pathname !== '/edittrip') return;
				setModal(true);
				setUser(row.id);
				// console.log(ownerId);
				// console.log(row.id);
				if (ownerId === row.id._id) setContent(1);
				else setContent(2);
			},
			sx: {
				cursor: location.pathname === '/edittrip' ? 'pointer' : '',
			},
		}),
	});
    const confirmKick = async () => {
        const response = await fetch(`${API}/kickMember`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({
                tripid: tripid,
                userid: user._id,
            }),
        });
		const json = await response.json();
		console.log(json);
		if (!json.success) {
			json.errors.forEach(error => {
				toast.error(error.msg, {});
			});
			if (json.logout === true) {
				localStorage.removeItem('authToken');
				localStorage.setItem('forcedLogOut', true);
				navigate('/profile');
			}
		} else {
			if (json.newAuthToken) localStorage.setItem('authToken', json.newAuthToken);
			let temp = data.filter(item => item._id !== user._id);
			setData(temp);
			setModal(false);
		}
	};
    const confirmCAdmin = async () => {
        const response = await fetch(`${API}/adminMember`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({
                tripid: tripid,
                userid: user._id,
            }),
        });
		const json = await response.json();
		console.log(json);
		if (!json.success) {
			json.errors.forEach(error => {
				toast.error(error.msg, {});
			});
			if (json.logout === true) {
				localStorage.removeItem('authToken');
				localStorage.setItem('forcedLogOut', true);
				navigate('/profile');
			}
		} else {
			if (json.newAuthToken) localStorage.setItem('authToken', json.newAuthToken);
			setModal(false);
			navigate('/');
		}
	};

	return (
		<>
			<Modal
				open={modalOpen}
				onClose={() => {
					setModal(false);
				}}
				aria-labelledby='modal-modal-titleinvite'
				aria-describedby='modal-formodal-descriptioninvite'
			>
				<Box sx={style}>
					<div style={{ width: '100%' }}>
						<Typography variant='h5' style={{ textAlign: 'center' }}>
							{user.name}
						</Typography>
						<Typography variant='h6' style={{ textAlign: 'center' }}>
							{user.email}
						</Typography>
					</div>
					{content === 0 && (
						<div>
							<Typography>Loading...</Typography>
						</div>
					)}
					{content === 1 && (
						<div>
							<Typography>You cannot kick yourself.</Typography>
						</div>
					)}
					{content === 2 && (
						<div style={{ display: 'flex', gap: '10px' }}>
							<Button variant='contained' onClick={() => setContent(3)}>
								Kick
							</Button>
							<Button variant='contained' onClick={() => setContent(4)}>
								Transfer Admin Rights
							</Button>
						</div>
					)}
					{content === 3 && (
						<div style={{ display: 'flex', gap: '10px' }}>
							<Button variant='contained' onClick={confirmKick}>
								Confirm Kick
							</Button>
							<Button variant='contained' onClick={() => setContent(2)}>
								Cancel
							</Button>
						</div>
					)}
					{content === 4 && (
						<div style={{ display: 'flex', gap: '10px' }}>
							<Button variant='contained' onClick={confirmCAdmin}>
								Confirm Transfer Admin Rights
							</Button>
							<Button variant='contained' onClick={() => setContent(2)}>
								Cancel
							</Button>
						</div>
					)}
				</Box>
			</Modal>
			<MaterialReactTable table={table} />
		</>
	);
};

export default MemberTable;
